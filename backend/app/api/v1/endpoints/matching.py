"""Stage 3 AI Matching and Candidate Ranking API Endpoints.

POST /api/match/evaluate:
Evaluates and ranks a batch of candidate resumes against a Job Description.
Generates embeddings using all-MiniLM-L6-v2, computes semantic similarity,
evaluates skill coverage, experience, and education, and outputs a transparent
0-100 weighted match score with stable ranking and explainability.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.schemas.matching import MatchRequest, MatchResponse, ScoredCandidate
from app.schemas.jd import JDAnalyzeResponse
from app.services.extractors.jd_analyzer import analyze_job_description
from app.services.matching.embedding_service import compute_embeddings, compute_cosine_similarity
from app.services.matching.matching_service import compute_candidate_match

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/evaluate",
    response_model=MatchResponse,
    summary="Evaluate and rank candidates using AI Matching Engine",
    description="Calculates semantic similarity via Sentence Transformers (all-MiniLM-L6-v2), evaluates required/preferred skills, experience, and education, and stably ranks candidates from highest to lowest overall match score.",
)
async def evaluate_candidates(payload: MatchRequest):
    """Evaluate and rank candidates against a job description."""
    if not payload.candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidates provided for matching evaluation. Please provide at least one candidate.",
        )

    # 1. Resolve Job Description Analysis
    jd_analysis: JDAnalyzeResponse
    jd_raw_text = payload.jd_text or ""

    if payload.jd_analysis is not None:
        jd_analysis = payload.jd_analysis
        if not jd_raw_text and jd_analysis.summary:
            jd_raw_text = jd_analysis.summary
    elif jd_raw_text.strip():
        # Analyze JD on-the-fly if raw text is provided without pre-analysis
        jd_analysis = analyze_job_description(jd_raw_text)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is required. Please provide either 'jd_text' or 'jd_analysis'.",
        )

    # 2. Build Rich Semantic Representation for the JD
    # We combine role title/summary, skills, and qualifications for rich contextual embedding
    jd_semantic_parts = [jd_raw_text]
    if jd_analysis.required_skills:
        jd_semantic_parts.append("Required Skills: " + ", ".join(jd_analysis.required_skills))
    if jd_analysis.preferred_skills:
        jd_semantic_parts.append("Preferred Skills: " + ", ".join(jd_analysis.preferred_skills))
    if jd_analysis.required_qualifications:
        jd_semantic_parts.append("Requirements: " + " ".join(jd_analysis.required_qualifications))
    jd_semantic_text = "\n".join(jd_semantic_parts).strip()

    # 3. Build Rich Semantic Representations for Candidates
    candidate_semantic_texts: List[str] = []
    for cand in payload.candidates:
        parts = []
        if cand.raw_text and cand.raw_text.strip():
            parts.append(cand.raw_text.strip()[:2500])
        else:
            # Fallback if raw text is truncated or missing
            if cand.skills:
                parts.append("Skills: " + ", ".join(cand.skills))
            if cand.education:
                parts.append("Education: " + "; ".join(cand.education))
            if cand.professional_experience_years is not None:
                parts.append(f"Professional Experience: {cand.professional_experience_years} years")
        candidate_semantic_texts.append("\n".join(parts) if parts else "Candidate Resume")

    # 4. Generate Embeddings using Sentence Transformers or Resilient Fallback
    try:
        all_texts = [jd_semantic_text] + candidate_semantic_texts
        logger.info(f"Generating embeddings for JD and {len(payload.candidates)} candidate(s)...")
        all_embeddings, active_model_name = compute_embeddings(all_texts)
        jd_embedding = all_embeddings[0]
        candidate_embeddings = all_embeddings[1:]
    except Exception as exc:
        logger.error(f"Semantic embedding generation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic embedding model failure: {str(exc)}",
        ) from exc

    # 5. Compute Dimensional & Composite Scores for Each Candidate
    scored_list: List[ScoredCandidate] = []
    for idx, cand in enumerate(payload.candidates):
        cand_emb = candidate_embeddings[idx]
        sim = compute_cosine_similarity(jd_embedding, cand_emb)
        scored_cand = compute_candidate_match(
            candidate=cand,
            jd_analysis=jd_analysis,
            semantic_similarity=sim,
        )
        scored_list.append(scored_cand)

    # 6. Stable Multi-key Ranking:
    # Primary: overall_match_score (descending)
    # Secondary: semantic_similarity (descending)
    # Tertiary: candidate name (alphabetical ascending)
    scored_list.sort(
        key=lambda c: (
            -c.overall_match_score,
            -c.semantic_similarity,
            (c.candidate.name or "").lower(),
            c.candidate_id,
        )
    )

    # 7. Assign 1-based ranks
    for rank_idx, cand in enumerate(scored_list, start=1):
        cand.rank = rank_idx

    # 8. Construct Summary
    avg_score = round(sum(c.overall_match_score for c in scored_list) / len(scored_list), 1)
    top_candidate = scored_list[0] if scored_list else None
    summary_msg = (
        f"Evaluated {len(scored_list)} candidate(s) against job criteria. "
        f"Batch average match score: {avg_score}%. "
        f"Top candidate: {top_candidate.candidate.name if top_candidate else 'None'} ({top_candidate.overall_match_score if top_candidate else 0}%)."
    )

    return MatchResponse(
        total_candidates=len(scored_list),
        ranked_candidates=scored_list,
        model_name=active_model_name,
        summary=summary_msg,
    )
