"""Unversioned, operational routers (service root and liveness).

These endpoints are intentionally *not* under ``/api/v1`` because they are
consumed by infrastructure (load balancers, container orchestrators, uptime
monitors) whose probe URLs should remain stable across API versions.
"""

from app.presentation.api.routers.system import router as system_router

__all__ = ["system_router"]
