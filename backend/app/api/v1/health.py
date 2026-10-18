"""Health check API router."""

from fastapi import APIRouter, Depends, Query
from backend.app.schemas.health import HealthResponse
from backend.app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


def get_health_service() -> HealthService:
    return HealthService()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health",
    description="Returns detailed health diagnostics for API, database, and local Ollama VLM model.",
)
async def check_health(
    check_inference: bool = Query(
        default=False,
        description="If true, actively executes a lightweight inference probe against the model.",
    ),
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """Evaluate and return service health status."""
    return await service.get_overall_health(check_active_inference=check_inference)
