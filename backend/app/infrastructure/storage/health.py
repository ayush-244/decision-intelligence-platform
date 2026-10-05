"""Storage health probe."""

from __future__ import annotations

import time

from app.domain.entities.health import ComponentHealth, HealthStatus
from app.domain.ports.health_probe import HealthProbe
from app.domain.ports.storage_provider import StorageProvider


class StorageHealthProbe(HealthProbe):
    def __init__(self, storage: StorageProvider) -> None:
        self._storage = storage

    @property
    def component_name(self) -> str:
        return "storage"

    async def check(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            await self._storage.health_check()
            latency_ms = int((time.perf_counter() - start) * 1000)
            return ComponentHealth(
                name=self.component_name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
            )
        except Exception:
            return ComponentHealth(
                name=self.component_name,
                status=HealthStatus.UNHEALTHY,
                detail="Storage unavailable",
            )
