"""Root and liveness endpoints (unversioned).

* ``GET /``       — welcome payload with service identity and doc links.
* ``GET /health`` — **liveness**: returns 200 whenever the process is serving.
  It performs no dependency I/O, matching how orchestrators expect a liveness
  probe to behave. Deep **readiness** (with dependency checks) lives at
  ``GET /api/v1/health``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.deps import SettingsDep, SystemInfoServiceDep
from app.presentation.api.schemas.health import LivenessResponse
from app.presentation.api.schemas.meta import RootResponse

router = APIRouter(tags=["system"])

_TAGLINE = "AI-Powered Decision Intelligence Platform"


@router.get("/", response_model=RootResponse, summary="Service root")
async def read_root(
    settings: SettingsDep,
    system_info: SystemInfoServiceDep,
) -> RootResponse:
    """Return service identity and a pointer to the API docs."""
    info = system_info.get_info()
    return RootResponse(
        name=info.name,
        tagline=_TAGLINE,
        version=info.version,
        docs_url="/docs" if settings.debug else None,
    )


@router.get("/health", response_model=LivenessResponse, summary="Liveness probe")
async def liveness() -> LivenessResponse:
    """Return 200 as long as the process is up. No dependency I/O."""
    return LivenessResponse()
