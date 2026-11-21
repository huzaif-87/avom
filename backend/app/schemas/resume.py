"""Pydantic schemas for resume parsing, candidate information, and storage."""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class CandidateResumeResult(BaseModel):
    """Structured extraction result for a single candidate resume."""

    candidate_id: str = Field(default="", description="Unique generated identifier for candidate")
    filename: str = Field(default="resume.pdf", description="Original filename of uploaded resume")
    file_type: str = Field(default="pdf", description="Document file extension: 'pdf' or 'docx'")
    page_count: Optional[int] = Field(default=None, description="Total page count of document")
    has_original_file: bool = Field(default=True, description="Whether original file is stored for preview/download")

    @model_validator(mode="before")
    @classmethod
    def normalize_candidate_fields(cls, data):
        if isinstance(data, dict):
            cid = data.get("candidate_id") or data.get("id")
            if not cid:
                cid = f"cand_{uuid.uuid4().hex[:8]}"
            data["candidate_id"] = str(cid)
            if not data.get("filename"):
                data["filename"] = "resume.pdf"
        return data

    # Candidate Contact Information
    name: str = Field(default="Unknown", description="Extracted candidate full name")
    email: Optional[str] = Field(default=None, description="Extracted candidate email address")
    phone: Optional[str] = Field(default=None, description="Extracted candidate phone number")
    skills: List[str] = Field(default_factory=list, description="Extracted technical and professional skills")
    education: List[str] = Field(default_factory=list, description="Extracted education and degree statements")

    # Accurate Experience Modeling
    professional_experience_years: Optional[float] = Field(
        default=None, description="Verified full-time professional experience in years (excludes education/projects)"
    )
    internship_experience_years: Optional[float] = Field(
        default=None, description="Separately tracked internship and training duration in years"
    )
    experience_confidence: str = Field(
        default="none", description="Confidence level: 'high', 'medium', 'low', or 'none'"
    )
    experience_source: str = Field(
        default="none",
        description="Source of experience estimate: 'explicit_statement', 'employment_history', 'internship_only', 'fresher_override', or 'none'",
    )
    experience_warnings: List[str] = Field(
        default_factory=list, description="Specific warnings explaining experience determination"
    )

    # Backward compatibility alias
    experience_years: Optional[float] = Field(
        default=None, description="Verified professional experience in years (mirrors professional_experience_years)"
    )

    # Raw Text and Processing Status
    raw_text: str = Field(default="", description="Extracted raw text content from the resume")
    warnings: List[str] = Field(default_factory=list, description="General extraction or document quality warnings")
    extraction_status: str = Field(
        default="success", description="Document text extraction status: 'success', 'partial', or 'failed'"
    )
    status: str = Field(
        default="success", description="Overall candidate status: 'success', 'partial', or 'error'"
    )


class ResumeBatchResponse(BaseModel):
    """Response envelope for batch resume parsing."""

    total_files: int = Field(..., description="Total count of files submitted in batch")
    successful: int = Field(..., description="Count of successfully parsed files")
    failed: int = Field(..., description="Count of files that failed processing")
    results: List[CandidateResumeResult] = Field(
        default_factory=list, description="Individual resume parsing results"
    )
