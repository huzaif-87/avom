"""Pydantic schemas for recruiter authentication and profile management."""

import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class RecruiterRegisterRequest(BaseModel):
    """Recruiter sign-up payload."""

    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the recruiter")
    email: str = Field(..., description="Valid corporate or personal recruiter email")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Password confirmation")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError("Invalid email format")
        return trimmed

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class RecruiterLoginRequest(BaseModel):
    """Recruiter login credentials."""

    email: str = Field(..., description="Registered recruiter email")
    password: str = Field(..., min_length=1, description="Recruiter password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        trimmed = v.strip().lower()
        if not EMAIL_REGEX.match(trimmed):
            raise ValueError("Invalid email format")
        return trimmed



class RecruiterResponse(BaseModel):
    """Safe recruiter profile representation (hashed password excluded)."""

    id: str
    full_name: str
    email: str
    created_at: Optional[str] = None


class AuthTokenResponse(BaseModel):
    """Authentication token response with recruiter profile."""

    access_token: str
    token_type: str = "bearer"
    recruiter: RecruiterResponse
