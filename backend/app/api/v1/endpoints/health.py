"""Health check endpoint."""

from fastapi import APIRouter, status
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the operational status of the TalentRank AI backend service.",
)
async def get_health() -> HealthResponse:
    """Return operational health status."""
    return HealthResponse()
