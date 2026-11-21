"""API v1 router aggregator.

Mounts health, resume parsing, and job description analysis endpoints.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, resumes, jd, matching, auth, analyses

api_router = APIRouter()

# Core health check router
api_router.include_router(health.router, tags=["Health"])

# Recruiter authentication router (/api/auth)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Recruiter Job Analysis & Shortlist router (/api/analyses)
api_router.include_router(analyses.router, prefix="/analyses", tags=["Analyses"])

# Resume parsing router (/api/resumes/parse)
api_router.include_router(resumes.router, prefix="/resumes", tags=["Resumes"])

# Job description analysis router (/api/jd/analyze)
api_router.include_router(jd.router, prefix="/jd", tags=["Job Description"])

# Stage 3 AI Matching and Candidate Ranking router (/api/match/evaluate)
api_router.include_router(matching.router, prefix="/match", tags=["AI Matching"])

