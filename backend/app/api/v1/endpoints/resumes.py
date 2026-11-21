"""Resume parsing, viewing, and session storage API endpoints."""

import os
import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends, Query
from fastapi.responses import FileResponse

from app.schemas.resume import CandidateResumeResult, ResumeBatchResponse
from app.services.parsers.pdf_parser import extract_text_from_pdf
from app.services.parsers.docx_parser import extract_text_from_docx
from app.services.extractors.candidate_extractor import extract_candidate_profile
from app.services.storage.resume_storage import (
    store_resume_file,
    get_resume_file,
    delete_resume_file,
    clear_all_resumes,
)
from app.services.storage.persistent_storage import (
    store_persistent_resume,
    get_persistent_resume,
    delete_persistent_resume,
)
from app.core.security import decode_access_token
from app.core.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter()

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


async def _resolve_recruiter_id(token: Optional[str]) -> Optional[str]:
    """Helper to safely extract recruiter_id if a valid token is provided."""
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        return payload.get("sub")
    except Exception:
        return None



@router.post(
    "/parse",
    response_model=ResumeBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse batch candidate resumes",
    description="Accepts multiple PDF or DOCX resume files, extracts text, stores originals in session vault, and returns structured candidate details.",
)
async def parse_resumes(
    files: List[UploadFile] = File(
        ...,
        description="One or more PDF/DOCX resume files (supports 10+ files per batch)",
    ),
) -> ResumeBatchResponse:
    """Parse multiple candidate resumes from multipart upload."""
    results: List[CandidateResumeResult] = []
    successful_count = 0
    failed_count = 0

    for upload_file in files:
        filename = upload_file.filename or "unknown_file"
        lower_name = filename.lower()
        candidate_id = f"cand_{uuid.uuid4().hex[:8]}"

        # 1. Validate file extension
        matched_ext = next((ext for ext in SUPPORTED_EXTENSIONS if lower_name.endswith(ext)), None)
        if not matched_ext:
            logger.warning(f"Rejected unsupported file upload: {filename}")
            results.append(
                CandidateResumeResult(
                    candidate_id=candidate_id,
                    filename=filename,
                    file_type="unknown",
                    has_original_file=False,
                    name="Unknown",
                    email=None,
                    phone=None,
                    skills=[],
                    education=[],
                    professional_experience_years=None,
                    internship_experience_years=None,
                    experience_confidence="none",
                    experience_source="none",
                    experience_warnings=[],
                    experience_years=None,
                    raw_text="",
                    warnings=[f"Unsupported file format for '{filename}'. Only .pdf and .docx files are supported."],
                    extraction_status="failed",
                    status="error",
                )
            )
            failed_count += 1
            continue

        # 2. Read file content safely in memory
        try:
            content = await upload_file.read()
        except Exception as exc:
            logger.error(f"Failed reading stream for {filename}: {exc}")
            results.append(
                CandidateResumeResult(
                    candidate_id=candidate_id,
                    filename=filename,
                    file_type="pdf" if lower_name.endswith(".pdf") else "docx",
                    has_original_file=False,
                    name="Unknown",
                    email=None,
                    phone=None,
                    skills=[],
                    education=[],
                    professional_experience_years=None,
                    internship_experience_years=None,
                    experience_confidence="none",
                    experience_source="none",
                    experience_warnings=[],
                    experience_years=None,
                    raw_text="",
                    warnings=[f"Failed to read uploaded file data: {str(exc)}"],
                    extraction_status="failed",
                    status="error",
                )
            )
            failed_count += 1
            continue

        file_type = "pdf" if lower_name.endswith(".pdf") else "docx"
        content_type = (
            "application/pdf"
            if file_type == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        # 3. Store in session vault for recruiter preview
        stored = store_resume_file(
            candidate_id=candidate_id,
            original_filename=filename,
            content=content,
            content_type=content_type,
        )

        # 4. Parse document based on extension
        raw_text = ""
        parser_warnings: List[str] = []
        parse_error: str | None = None
        page_count = 1
        extraction_status = "success"

        if file_type == "pdf":
            raw_text, parser_warnings, parse_error, page_count, extraction_status = extract_text_from_pdf(
                content, filename=filename
            )
        else:
            raw_text, parser_warnings, parse_error, page_count, extraction_status = extract_text_from_docx(
                content, filename=filename
            )

        if parse_error or extraction_status == "failed":
            logger.warning(f"Parser failure on {filename}: {parse_error or 'No text'}")
            results.append(
                CandidateResumeResult(
                    candidate_id=candidate_id,
                    filename=filename,
                    file_type=file_type,
                    page_count=page_count,
                    has_original_file=stored,
                    name="Unknown",
                    email=None,
                    phone=None,
                    skills=[],
                    education=[],
                    professional_experience_years=None,
                    internship_experience_years=None,
                    experience_confidence="none",
                    experience_source="none",
                    experience_warnings=[],
                    experience_years=None,
                    raw_text="",
                    warnings=parser_warnings or [parse_error or "Text extraction failed."],
                    extraction_status="failed",
                    status="error",
                )
            )
            failed_count += 1
            continue

        # 5. Extract structured candidate information
        candidate_result = extract_candidate_profile(
            raw_text=raw_text,
            filename=filename,
            initial_warnings=parser_warnings,
            file_type=file_type,
            page_count=page_count,
            extraction_status=extraction_status,
            candidate_id=candidate_id,
        )

        if candidate_result.status == "error":
            failed_count += 1
        else:
            successful_count += 1

        results.append(candidate_result)

    return ResumeBatchResponse(
        total_files=len(files),
        successful=successful_count,
        failed=failed_count,
        results=results,
    )


@router.get(
    "/{candidate_id}/view",
    summary="View candidate original resume",
    description="Streams the original uploaded resume file inline for browser preview with ownership checks.",
)
async def view_candidate_resume(
    candidate_id: str,
    token: Optional[str] = Query(None, description="Optional access token for iframe / direct link preview"),
):
    """Retrieve and view original candidate resume file."""
    recruiter_id = await _resolve_recruiter_id(token)

    # 1. If recruiter identity resolved, check their private persistent storage
    info = None
    if recruiter_id:
        info = get_persistent_resume(recruiter_id, candidate_id)

    # 2. Check session vault or unauthenticated staging
    if not info:
        info = get_resume_file(candidate_id)

    # 3. If still not found, check MongoDB for candidate ownership to find recruiter_id
    if not info:
        database = get_database()
        if database is not None:
            cand = await database.candidates.find_one({"candidate_id": candidate_id})
            if cand and cand.get("recruiter_id"):
                if recruiter_id and cand["recruiter_id"] != recruiter_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access forbidden: You do not own this candidate's resume.",
                    )
                info = get_persistent_resume(cand["recruiter_id"], candidate_id)

    if not info or not os.path.exists(info["file_path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Original resume file for candidate '{candidate_id}' was not found.",
        )

    file_path = info["file_path"]
    filename = info.get("filename", "resume.pdf")
    content_type = info.get("content_type", "application/pdf")

    # Inline disposition allows browser PDF preview
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
        content_disposition_type="inline",
    )


@router.get(
    "/{candidate_id}/download",
    summary="Download candidate original resume",
    description="Downloads the original uploaded resume file as an attachment.",
)
async def download_candidate_resume(
    candidate_id: str,
    token: Optional[str] = Query(None, description="Optional access token"),
):
    """Download original candidate resume file."""
    recruiter_id = await _resolve_recruiter_id(token)

    info = None
    if recruiter_id:
        info = get_persistent_resume(recruiter_id, candidate_id)

    if not info:
        info = get_resume_file(candidate_id)

    if not info:
        database = get_database()
        if database is not None:
            cand = await database.candidates.find_one({"candidate_id": candidate_id})
            if cand and cand.get("recruiter_id"):
                if recruiter_id and cand["recruiter_id"] != recruiter_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access forbidden: You do not own this candidate's resume.",
                    )
                info = get_persistent_resume(cand["recruiter_id"], candidate_id)

    if not info or not os.path.exists(info["file_path"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Original resume file for candidate '{candidate_id}' was not found.",
        )

    file_path = info["file_path"]
    filename = info.get("filename", "resume")
    content_type = info.get("content_type", "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
        content_disposition_type="attachment",
    )


@router.delete(
    "/{candidate_id}",
    summary="Delete candidate and temporary file",
    description="Deletes a candidate's uploaded resume file from the session storage.",
)
async def remove_candidate(candidate_id: str):
    """Remove candidate and delete stored file from session vault."""
    success = delete_resume_file(candidate_id)
    return {
        "success": success,
        "candidate_id": candidate_id,
        "message": f"Candidate '{candidate_id}' removed from session storage.",
    }


@router.post(
    "/reset",
    summary="Reset session resume storage",
    description="Clears all stored resume files in the session vault.",
)
async def reset_session_vault():
    """Clear all session resumes from vault."""
    deleted_count = clear_all_resumes()
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Session vault cleared. Removed {deleted_count} file(s).",
    }
