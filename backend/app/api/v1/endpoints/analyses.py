"""Persistent Job Analysis and Recruiter Workspace API endpoints."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.core.database import get_database
from app.core.security import get_current_recruiter
from app.schemas.analysis import (
    SaveAnalysisRequest,
    JobAnalysisSummaryResponse,
    JobAnalysisDetailResponse,
    PersistentCandidateSchema,
    CandidateStatusUpdateRequest,
    CandidateStatusEnum,
)
from app.services.storage.persistent_storage import (
    delete_recruiter_analysis_resumes,
    delete_persistent_resume,
)

router = APIRouter()


@router.post(
    "",
    response_model=JobAnalysisDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save or update a job analysis",
    description="Persists job description criteria, parsed candidate profiles, and AI matching rankings into recruiter workspace.",
)
async def save_analysis(
    payload: SaveAnalysisRequest,
    current_recruiter: dict = Depends(get_current_recruiter),
) -> JobAnalysisDetailResponse:
    """Save complete analysis with candidates into MongoDB."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Ensure MongoDB is running.",
        )

    recruiter_id = current_recruiter["id"]
    analysis_id = payload.analysis_id or f"analysis_{uuid.uuid4().hex[:10]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Determine job title
    job_title = payload.job_title
    if not job_title:
        # Infer title from JD text first line or analysis summary
        first_line = payload.jd_text.strip().split("\n")[0].strip()
        job_title = first_line[:60] if len(first_line) > 3 else "Target Position"

    # Map candidate profiles
    saved_candidates = []
    shortlisted_cnt = 0
    maybe_cnt = 0
    rejected_cnt = 0
    unreviewed_cnt = 0
    scores = []

    # Map AI match details from ai_matching_results if present
    ranked_map: Dict[str, Dict[str, Any]] = {}
    if payload.ai_matching_results and "ranked_candidates" in payload.ai_matching_results:
        for rc in payload.ai_matching_results["ranked_candidates"]:
            cid = rc.get("candidate_id")
            if cid:
                ranked_map[cid] = rc

    for c in payload.candidates:
        cid = c.get("candidate_id") or f"cand_{uuid.uuid4().hex[:8]}"
        ranked_info = ranked_map.get(cid, {})

        score = ranked_info.get("overall_match_score", c.get("overall_match_score"))
        if score is not None:
            scores.append(score)

        status_val = c.get("status", CandidateStatusEnum.UNREVIEWED.value)
        if status_val == CandidateStatusEnum.SHORTLISTED.value:
            shortlisted_cnt += 1
        elif status_val == CandidateStatusEnum.MAYBE.value:
            maybe_cnt += 1
        elif status_val == CandidateStatusEnum.REJECTED.value:
            rejected_cnt += 1
        else:
            unreviewed_cnt += 1

        cand_doc = {
            "candidate_id": cid,
            "analysis_id": analysis_id,
            "recruiter_id": recruiter_id,
            "filename": c.get("filename", "resume.pdf"),
            "name": c.get("name", "Unknown"),
            "email": c.get("email"),
            "phone": c.get("phone"),
            "skills": c.get("skills", []),
            "education": c.get("education", []),
            "experience_years": c.get("experience_years"),
            "professional_experience_years": c.get("professional_experience_years"),
            "internship_experience_years": c.get("internship_experience_years"),
            "experience_source": c.get("experience_source", "none"),
            "experience_details": c.get("experience_details", []),
            "file_type": c.get("file_type", "unknown"),
            "page_count": c.get("page_count"),
            "raw_text": c.get("raw_text"),
            "warnings": c.get("warnings", []),
            "overall_match_score": score,
            "semantic_similarity": ranked_info.get("semantic_similarity", c.get("semantic_similarity")),
            "rank": ranked_info.get("rank", c.get("rank")),
            "matched_required_skills": ranked_info.get("matched_required_skills", c.get("matched_required_skills", [])),
            "missing_required_skills": ranked_info.get("missing_required_skills", c.get("missing_required_skills", [])),
            "matched_preferred_skills": ranked_info.get("matched_preferred_skills", c.get("matched_preferred_skills", [])),
            "missing_preferred_skills": ranked_info.get("missing_preferred_skills", c.get("missing_preferred_skills", [])),
            "strengths": ranked_info.get("strengths", c.get("strengths", [])),
            "gaps": ranked_info.get("gaps", c.get("gaps", [])),
            "explanation": ranked_info.get("explanation", c.get("explanation")),
            "breakdown": ranked_info.get("breakdown", c.get("breakdown")),
            "status": status_val,
            "status_updated_at": c.get("status_updated_at", now_iso),
            "created_at": c.get("created_at", now_iso),
        }

        # Upsert candidate document
        await database.candidates.update_one(
            {"analysis_id": analysis_id, "candidate_id": cid},
            {"$set": cand_doc},
            upsert=True,
        )
        saved_candidates.append(PersistentCandidateSchema(**cand_doc))

    avg_score = round(sum(scores) / len(scores)) if scores else None

    analysis_doc = {
        "id": analysis_id,
        "recruiter_id": recruiter_id,
        "job_title": job_title,
        "jd_text": payload.jd_text,
        "jd_analysis": payload.jd_analysis,
        "ai_matching_results": payload.ai_matching_results,
        "candidate_count": len(saved_candidates),
        "shortlisted_count": shortlisted_cnt,
        "maybe_count": maybe_cnt,
        "rejected_count": rejected_cnt,
        "unreviewed_count": unreviewed_cnt,
        "average_match_score": avg_score,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    # Upsert Job Analysis
    await database.job_analyses.update_one(
        {"id": analysis_id, "recruiter_id": recruiter_id},
        {"$set": analysis_doc},
        upsert=True,
    )

    return JobAnalysisDetailResponse(
        **analysis_doc,
        candidates=saved_candidates,
    )


@router.get(
    "",
    response_model=List[JobAnalysisSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List recruiter analyses",
    description="Lists all saved job analyses belonging exclusively to the authenticated recruiter.",
)
async def list_analyses(
    current_recruiter: dict = Depends(get_current_recruiter),
) -> List[JobAnalysisSummaryResponse]:
    """Retrieve all analyses for authenticated recruiter."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    recruiter_id = current_recruiter["id"]
    cursor = database.job_analyses.find({"recruiter_id": recruiter_id}).sort("created_at", -1)

    results = []
    async for doc in cursor:
        results.append(
            JobAnalysisSummaryResponse(
                id=doc["id"],
                job_title=doc.get("job_title", "Target Position"),
                jd_text=doc.get("jd_text", ""),
                jd_analysis=doc.get("jd_analysis", {}),
                candidate_count=doc.get("candidate_count", 0),
                shortlisted_count=doc.get("shortlisted_count", 0),
                maybe_count=doc.get("maybe_count", 0),
                rejected_count=doc.get("rejected_count", 0),
                unreviewed_count=doc.get("unreviewed_count", 0),
                average_match_score=doc.get("average_match_score"),
                created_at=doc.get("created_at", ""),
                updated_at=doc.get("updated_at", ""),
            )
        )

    return results


@router.get(
    "/{analysis_id}",
    response_model=JobAnalysisDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single analysis details",
    description="Retrieves a full analysis record including candidate profiles and matching rankings. Verifies ownership.",
)
async def get_analysis_by_id(
    analysis_id: str,
    status_filter: Optional[str] = Query(None, description="Filter candidates by status (shortlisted, maybe, rejected, unreviewed)"),
    current_recruiter: dict = Depends(get_current_recruiter),
) -> JobAnalysisDetailResponse:
    """Retrieve full analysis and candidate profiles."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    recruiter_id = current_recruiter["id"]
    analysis = await database.job_analyses.find_one({"id": analysis_id, "recruiter_id": recruiter_id})

    if not analysis:
        # Check if it exists for another recruiter (strictly deny access)
        exists_other = await database.job_analyses.find_one({"id": analysis_id})
        if exists_other:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not own this analysis.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found in your workspace.",
        )

    # Fetch candidates belonging to this analysis
    cand_query = {"analysis_id": analysis_id, "recruiter_id": recruiter_id}
    if status_filter:
        cand_query["status"] = status_filter.lower()

    cand_cursor = database.candidates.find(cand_query).sort([("rank", 1), ("overall_match_score", -1)])
    candidates = []
    async for cdoc in cand_cursor:
        candidates.append(PersistentCandidateSchema(**cdoc))

    return JobAnalysisDetailResponse(
        id=analysis["id"],
        recruiter_id=analysis["recruiter_id"],
        job_title=analysis.get("job_title", "Target Position"),
        jd_text=analysis.get("jd_text", ""),
        jd_analysis=analysis.get("jd_analysis", {}),
        candidates=candidates,
        ai_matching_results=analysis.get("ai_matching_results"),
        candidate_count=analysis.get("candidate_count", len(candidates)),
        shortlisted_count=analysis.get("shortlisted_count", 0),
        maybe_count=analysis.get("maybe_count", 0),
        rejected_count=analysis.get("rejected_count", 0),
        unreviewed_count=analysis.get("unreviewed_count", 0),
        average_match_score=analysis.get("average_match_score"),
        created_at=analysis.get("created_at", ""),
        updated_at=analysis.get("updated_at", ""),
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete analysis and associated files",
    description="Deletes an analysis, all candidate records, and all private resume files belonging to it.",
)
async def delete_analysis(
    analysis_id: str,
    current_recruiter: dict = Depends(get_current_recruiter),
):
    """Safely delete analysis and its private resumes."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    recruiter_id = current_recruiter["id"]
    analysis = await database.job_analyses.find_one({"id": analysis_id, "recruiter_id": recruiter_id})
    if not analysis:
        exists_other = await database.job_analyses.find_one({"id": analysis_id})
        if exists_other:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not own this analysis.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found.",
        )

    # Collect candidate IDs to clean up resume files
    cand_cursor = database.candidates.find({"analysis_id": analysis_id, "recruiter_id": recruiter_id}, {"candidate_id": 1})
    cids = [cdoc["candidate_id"] async for cdoc in cand_cursor]

    # Delete files on disk
    delete_recruiter_analysis_resumes(recruiter_id, cids)

    # Delete candidates and analysis from MongoDB
    await database.candidates.delete_many({"analysis_id": analysis_id, "recruiter_id": recruiter_id})
    await database.job_analyses.delete_one({"id": analysis_id, "recruiter_id": recruiter_id})

    return {
        "status": "success",
        "message": f"Analysis {analysis_id} and {len(cids)} candidates deleted successfully.",
        "deleted_candidates_count": len(cids),
    }


@router.patch(
    "/{analysis_id}/candidates/{candidate_id}/status",
    response_model=PersistentCandidateSchema,
    status_code=status.HTTP_200_OK,
    summary="Update candidate shortlist decision status",
    description="Updates candidate status (shortlisted, maybe, rejected, unreviewed) immediately in MongoDB without re-ranking or re-parsing.",
)
async def update_candidate_status(
    analysis_id: str,
    candidate_id: str,
    payload: CandidateStatusUpdateRequest,
    current_recruiter: dict = Depends(get_current_recruiter),
) -> PersistentCandidateSchema:
    """Update candidate decision status."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    recruiter_id = current_recruiter["id"]

    # Verify candidate exists and belongs to this recruiter and analysis
    candidate = await database.candidates.find_one(
        {"analysis_id": analysis_id, "candidate_id": candidate_id, "recruiter_id": recruiter_id}
    )

    if not candidate:
        # Check ownership violation
        other = await database.candidates.find_one({"candidate_id": candidate_id})
        if other:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Candidate belongs to another recruiter.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found in this analysis.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    new_status = payload.status.value

    # Update candidate status
    await database.candidates.update_one(
        {"analysis_id": analysis_id, "candidate_id": candidate_id, "recruiter_id": recruiter_id},
        {"$set": {"status": new_status, "status_updated_at": now_iso}},
    )

    # Re-calculate analysis status counts
    shortlisted_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.SHORTLISTED.value}
    )
    maybe_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.MAYBE.value}
    )
    rejected_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.REJECTED.value}
    )
    unreviewed_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.UNREVIEWED.value}
    )

    await database.job_analyses.update_one(
        {"id": analysis_id, "recruiter_id": recruiter_id},
        {
            "$set": {
                "shortlisted_count": shortlisted_cnt,
                "maybe_count": maybe_cnt,
                "rejected_count": rejected_cnt,
                "unreviewed_count": unreviewed_cnt,
                "updated_at": now_iso,
            }
        },
    )

    updated_candidate = await database.candidates.find_one(
        {"analysis_id": analysis_id, "candidate_id": candidate_id, "recruiter_id": recruiter_id}
    )
    return PersistentCandidateSchema(**updated_candidate)


@router.delete(
    "/{analysis_id}/candidates/{candidate_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete candidate from analysis",
    description="Removes a candidate and deletes their private resume file.",
)
async def delete_candidate(
    analysis_id: str,
    candidate_id: str,
    current_recruiter: dict = Depends(get_current_recruiter),
):
    """Delete single candidate from analysis."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable.",
        )

    recruiter_id = current_recruiter["id"]
    candidate = await database.candidates.find_one(
        {"analysis_id": analysis_id, "candidate_id": candidate_id, "recruiter_id": recruiter_id}
    )

    if not candidate:
        other = await database.candidates.find_one({"candidate_id": candidate_id})
        if other:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Candidate belongs to another recruiter.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )

    # Delete resume file from storage
    delete_persistent_resume(recruiter_id, candidate_id)

    # Delete from database
    await database.candidates.delete_one(
        {"analysis_id": analysis_id, "candidate_id": candidate_id, "recruiter_id": recruiter_id}
    )

    # Update counts in analysis
    total_cnt = await database.candidates.count_documents({"analysis_id": analysis_id, "recruiter_id": recruiter_id})
    shortlisted_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.SHORTLISTED.value}
    )
    maybe_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.MAYBE.value}
    )
    rejected_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.REJECTED.value}
    )
    unreviewed_cnt = await database.candidates.count_documents(
        {"analysis_id": analysis_id, "recruiter_id": recruiter_id, "status": CandidateStatusEnum.UNREVIEWED.value}
    )

    await database.job_analyses.update_one(
        {"id": analysis_id, "recruiter_id": recruiter_id},
        {
            "$set": {
                "candidate_count": total_cnt,
                "shortlisted_count": shortlisted_cnt,
                "maybe_count": maybe_cnt,
                "rejected_count": rejected_cnt,
                "unreviewed_count": unreviewed_cnt,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    return {"status": "success", "message": f"Candidate {candidate_id} removed successfully."}
