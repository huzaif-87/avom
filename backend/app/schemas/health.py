"""Health check response schema."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health status endpoint."""

    status: str = Field(default="ok", description="Operational status of backend service")
    message: str = Field(
        default="TalentRank AI Backend is running",
        description="Human readable status message",
    )
    service: str = Field(default="TalentRank AI", description="Service identifier")
    version: str = Field(default="1.0.0", description="API version")
    environment: str = Field(default="development", description="Current runtime environment")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check",
    )
