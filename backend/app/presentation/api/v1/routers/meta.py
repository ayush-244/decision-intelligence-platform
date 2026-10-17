"""Version endpoint: ``GET /api/v1/version``."""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.deps import SystemInfoServiceDep
from app.presentation.api.schemas.meta import VersionResponse

router = APIRouter(prefix="/version", tags=["meta"])


@router.get("", response_model=VersionResponse, summary="Service version")
async def read_version(system_info: SystemInfoServiceDep) -> VersionResponse:
    """Return service name, semantic version, and active environment."""
    info = system_info.get_info()
    return VersionResponse(name=info.name, version=info.version, environment=info.environment)
