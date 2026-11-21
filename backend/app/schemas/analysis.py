"""Pydantic schemas for persistent Job Analysis, Candidates, and Shortlist statuses."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class CandidateStatusEnum(str, Enum):
    """Candidate review/decision status."""

    UNREVIEWED = "unreviewed"
    SHORTLISTED = "shortlisted"
    MAYBE = "maybe"
    REJECTED = "rejected"


class CandidateStatusUpdateRequest(BaseModel):
    """Request schema for updating a candidate's review status."""

    status: CandidateStatusEnum = Field(..., description="Target status: unreviewed, shortlisted, maybe, or rejected")


class PersistentCandidateSchema(BaseModel):
    """Candidate profile stored persistently in MongoDB."""

    candidate_id: str
    analysis_id: str
    recruiter_id: str
    filename: str
    name: str = "Unknown"
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    education: List[str] = []
    experience_years: Optional[float] = None
    professional_experience_years: Optional[float] = None
    internship_experience_years: Optional[float] = None
    experience_source: str = "none"
    experience_details: List[str] = []
    file_type: str = "unknown"
    page_count: Optional[int] = None
    raw_text: Optional[str] = None
    warnings: List[str] = []

    # AI Match & Ranking results
    overall_match_score: Optional[float] = None
    semantic_similarity: Optional[float] = None
    rank: Optional[int] = None
    matched_required_skills: List[str] = []
    missing_required_skills: List[str] = []
    matched_preferred_skills: List[str] = []
    missing_preferred_skills: List[str] = []
    strengths: List[str] = []
    gaps: List[str] = []
    explanation: Optional[str] = None
    breakdown: Optional[Dict[str, Any]] = None

    # Recruiter Shortlist decision status
    status: CandidateStatusEnum = CandidateStatusEnum.UNREVIEWED
    status_updated_at: Optional[str] = None
    created_at: str


class SaveAnalysisRequest(BaseModel):
    """Payload to create or persist a Job Description analysis with candidate matches."""

    analysis_id: Optional[str] = None
    job_title: Optional[str] = None
    jd_text: str = Field(default="", description="Full job description text")
    jd_analysis: Dict[str, Any] = Field(default_factory=dict, description="Structured job criteria extracted from JD")
    candidates: List[Dict[str, Any]] = Field(default_factory=list, description="Parsed and matched candidate profiles")
    ai_matching_results: Optional[Dict[str, Any]] = Field(default=None, description="Complete AI match engine output")


class JobAnalysisSummaryResponse(BaseModel):
    """Summary of a saved job analysis for the recruiter dashboard and history list."""

    id: str
    job_title: str
    jd_text: str
    jd_analysis: Dict[str, Any]
    candidate_count: int = 0
    shortlisted_count: int = 0
    maybe_count: int = 0
    rejected_count: int = 0
    unreviewed_count: int = 0
    average_match_score: Optional[float] = None
    created_at: str
    updated_at: str


class JobAnalysisDetailResponse(BaseModel):
    """Full detail of a saved job analysis including all candidate profiles."""

    id: str
    recruiter_id: str
    job_title: str
    jd_text: str
    jd_analysis: Dict[str, Any]
    candidates: List[PersistentCandidateSchema] = []
    ai_matching_results: Optional[Dict[str, Any]] = None
    candidate_count: int = 0
    shortlisted_count: int = 0
    maybe_count: int = 0
    rejected_count: int = 0
    unreviewed_count: int = 0
    average_match_score: Optional[float] = None
    created_at: str
    updated_at: str
