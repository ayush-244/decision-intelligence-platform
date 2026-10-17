"""Readiness endpoint: ``GET /api/v1/health``.

Runs the ``CheckSystemHealthUseCase`` to probe PostgreSQL and Redis. Returns
``200`` when the service is ready (healthy/degraded) and ``503`` when a critical
dependency is unhealthy — the semantics orchestrators use to decide whether to
route traffic to the instance.
"""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter, Response

from app.presentation.api.deps import CheckSystemHealthDep
from app.presentation.api.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Readiness probe",
    responses={HTTPStatus.SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def readiness(
    use_case: CheckSystemHealthDep,
    response: Response,
) -> HealthResponse:
    """Aggregate dependency health and set the HTTP status accordingly."""
    system_health = await use_case.execute()
    if not system_health.is_ready:
        response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
    return HealthResponse.from_domain(system_health)
