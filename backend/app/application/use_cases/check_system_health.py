"""Use-case: aggregate the health of all system dependencies.

Runs every configured :class:`HealthProbe` concurrently, applies a per-probe
timeout so one slow dependency cannot stall the readiness check, and folds the
results into a single :class:`SystemHealth`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from app.core.constants import HEALTH_PROBE_TIMEOUT_SECONDS
from app.core.logging import get_logger
from app.domain.entities.health import ComponentHealth, HealthStatus, SystemHealth
from app.domain.ports.health_probe import HealthProbe

_logger = get_logger(__name__)


class CheckSystemHealthUseCase:
    """Coordinate all dependency probes into an overall system health report."""

    def __init__(
        self,
        probes: Sequence[HealthProbe],
        *,
        timeout_seconds: float = HEALTH_PROBE_TIMEOUT_SECONDS,
    ) -> None:
        self._probes = probes
        self._timeout_seconds = timeout_seconds

    async def execute(self) -> SystemHealth:
        """Probe all dependencies concurrently and aggregate the result."""
        if not self._probes:
            return SystemHealth.from_components(())

        results = await asyncio.gather(
            *(self._run_probe(probe) for probe in self._probes),
        )
        return SystemHealth.from_components(tuple(results))

    async def _run_probe(self, probe: HealthProbe) -> ComponentHealth:
        """Execute a single probe with a timeout and defensive error handling."""
        try:
            async with asyncio.timeout(self._timeout_seconds):
                return await probe.check()
        except TimeoutError:
            _logger.warning("health_probe_timeout", component=probe.component_name)
            return ComponentHealth(
                name=probe.component_name,
                status=HealthStatus.UNHEALTHY,
                detail=f"Timed out after {self._timeout_seconds:g}s",
            )
        except Exception as exc:  # probes must never crash the readiness check
            _logger.error(
                "health_probe_error",
                component=probe.component_name,
                error=str(exc),
            )
            return ComponentHealth(
                name=probe.component_name,
                status=HealthStatus.UNHEALTHY,
                detail="Unexpected error during health probe",
            )
