"""Job description analysis API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.jd import JDAnalyzeRequest, JDAnalyzeResponse
from app.services.extractors.jd_analyzer import analyze_job_description

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=JDAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze job description text",
    description="Accepts job description text and performs rule-based extraction of skills, required qualifications, preferred qualifications, education benchmarks, and minimum experience.",
)
async def analyze_jd(payload: JDAnalyzeRequest) -> JDAnalyzeResponse:
    """Analyze provided job description text."""
    if not payload.text or not payload.text.strip():
        logger.warning("Received empty job description text.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description text cannot be empty or blank.",
        )

    return analyze_job_description(payload.text)
