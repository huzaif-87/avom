"""Pydantic schemas for Stage 3 AI Resume Matching and Candidate Ranking."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.resume import CandidateResumeResult
from app.schemas.jd import JDAnalyzeResponse


class MatchBreakdown(BaseModel):
    """Detailed transparent breakdown of the weighted scoring components."""

    semantic_similarity: float = Field(
        ..., description="Normalized semantic embedding cosine similarity (0.0 to 1.0)"
    )
    semantic_score: float = Field(
        ..., description="Weighted semantic similarity contribution (out of 35.0)"
    )

    required_skill_coverage: float = Field(
        ..., description="Proportion of required skills matched (0.0 to 1.0)"
    )
    required_skills_score: float = Field(
        ..., description="Weighted required skills contribution (out of 30.0)"
    )

    experience_relevance: float = Field(
        ..., description="Normalized experience benchmark match (0.0 to 1.0)"
    )
    experience_score: float = Field(
        ..., description="Weighted experience contribution (out of 20.0)"
    )

    education_relevance: float = Field(
        ..., description="Normalized education criteria match (0.0 to 1.0)"
    )
    education_score: float = Field(
        ..., description="Weighted education contribution (out of 10.0)"
    )

    preferred_skill_coverage: float = Field(
        ..., description="Proportion of preferred skills matched (0.0 to 1.0)"
    )
    preferred_skills_score: float = Field(
        ..., description="Weighted preferred skills contribution (out of 5.0)"
    )


class ScoredCandidate(BaseModel):
    """Candidate evaluation with Stage 3 AI matching metrics."""

    candidate_id: str = Field(..., description="Unique generated identifier for candidate")
    rank: int = Field(..., description="Stable 1-based ranking index based on overall match score")
    overall_match_score: float = Field(
        ..., description="Final combined weighted score from 0.0 to 100.0"
    )

    # Core required match details
    semantic_similarity: float = Field(
        ..., description="Raw cosine similarity score between JD and resume embeddings (0.0 to 1.0)"
    )
    matched_required_skills: List[str] = Field(
        default_factory=list, description="Required skills from JD found in candidate profile"
    )
    missing_required_skills: List[str] = Field(
        default_factory=list, description="Required skills from JD missing in candidate profile"
    )
    matched_preferred_skills: List[str] = Field(
        default_factory=list, description="Preferred skills from JD found in candidate profile"
    )
    missing_preferred_skills: List[str] = Field(
        default_factory=list, description="Preferred skills from JD not found in candidate profile"
    )

    # Dimensional evaluations
    experience_match: str = Field(
        ..., description="Qualitative comparison against JD minimum experience requirement"
    )
    education_match: str = Field(
        ..., description="Qualitative comparison against JD education requirements"
    )

    # Explainability & Insights
    strengths: List[str] = Field(
        default_factory=list, description="Key candidate qualifications aligning with the JD"
    )
    gaps: List[str] = Field(
        default_factory=list, description="Identified deficiencies, missing requirements, or warnings"
    )
    explanation: str = Field(
        ..., description="Short recruiter-friendly explanation of why the candidate received this score"
    )

    # Full scoring breakdown
    breakdown: MatchBreakdown = Field(
        ..., description="Detailed component weights and normalized scores"
    )

    # Embedded original candidate profile
    candidate: CandidateResumeResult = Field(
        ..., description="Extracted candidate resume details (contact, full skills, experience, file)"
    )


class MatchRequest(BaseModel):
    """Payload to perform AI matching between a JD and a batch of candidates."""

    jd_text: Optional[str] = Field(
        default=None, description="Raw job description text (optional if jd_analysis provided)"
    )
    jd_analysis: Optional[JDAnalyzeResponse] = Field(
        default=None, description="Pre-analyzed job description structure"
    )
    candidates: List[CandidateResumeResult] = Field(
        ..., description="List of parsed candidate profiles to evaluate and rank"
    )


class MatchResponse(BaseModel):
    """Stage 3 AI matching and candidate ranking response."""

    total_candidates: int = Field(..., description="Total number of candidates evaluated")
    ranked_candidates: List[ScoredCandidate] = Field(
        ..., description="Ranked list of candidates sorted by overall match score"
    )
    model_name: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence Transformers model used for semantic embeddings"
    )
    scoring_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "semantic_similarity": 35.0,
            "required_skills": 30.0,
            "experience": 20.0,
            "education": 10.0,
            "preferred_skills": 5.0,
        },
        description="Scoring weights distribution totaling 100.0",
    )
    summary: str = Field(
        default="", description="High-level evaluation summary across the candidate batch"
    )
