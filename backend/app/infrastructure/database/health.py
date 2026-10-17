"""PostgreSQL health probe.

Executes a trivial ``SELECT 1`` to verify the connection pool can reach the
database, measuring round-trip latency. Implements the domain
:class:`HealthProbe` port so the health use-case remains agnostic of SQL.
"""

from __future__ import annotations

import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.constants import HEALTH_PROBE_FAILURE_DETAIL
from app.core.logging import get_logger
from app.domain.entities.health import ComponentHealth, HealthStatus
from app.domain.ports.health_probe import HealthProbe

_logger = get_logger(__name__)
_COMPONENT_NAME = "postgres"


class DatabaseHealthProbe(HealthProbe):
    """Checks PostgreSQL connectivity via the async engine."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @property
    def component_name(self) -> str:
        return _COMPONENT_NAME

    async def check(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            async with self._engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as exc:  # report failures, never raise from a probe
            _logger.warning(
                "health_probe_failed",
                component=self.component_name,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return ComponentHealth(
                name=self.component_name,
                status=HealthStatus.UNHEALTHY,
                detail=HEALTH_PROBE_FAILURE_DETAIL,
            )
        latency_ms = (time.perf_counter() - start) * 1000
        return ComponentHealth(
            name=self.component_name,
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
        )
