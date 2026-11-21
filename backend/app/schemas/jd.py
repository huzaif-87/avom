"""Pydantic schemas for Job Description (JD) analysis."""

from typing import List, Optional
from pydantic import BaseModel, Field


class JDAnalyzeRequest(BaseModel):
    """Request payload for Job Description analysis."""

    text: str = Field(
        ...,
        description="Full text content of the job description",
    )


class JDAnalyzeResponse(BaseModel):
    """Structured analysis response for a Job Description."""

    extracted_skills: List[str] = Field(
        default_factory=list,
        description="All recognized technical and professional skills in the JD",
    )
    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills identified under required / must-have criteria",
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Skills identified under preferred / nice-to-have criteria",
    )
    minimum_experience: Optional[float] = Field(
        default=None,
        description="Minimum years of professional experience required, if explicitly stated",
    )
    education_requirements: List[str] = Field(
        default_factory=list,
        description="Educational degree benchmarks and qualification statements",
    )
    required_qualifications: List[str] = Field(
        default_factory=list,
        description="Extracted required criteria statements and bullet points",
    )
    preferred_qualifications: List[str] = Field(
        default_factory=list,
        description="Extracted preferred or bonus qualifications statements",
    )
    summary: str = Field(
        default="",
        description="Human-readable summary of the JD analysis findings",
    )
