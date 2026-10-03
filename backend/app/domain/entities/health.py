"""System-health domain model.

These are immutable value objects describing the liveness/readiness of the
service and its dependencies. They are framework-agnostic: the same objects are
produced by infrastructure probes and consumed by the presentation layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class HealthStatus(StrEnum):
    """Ordered health states, from best to worst.

    The ordering is used to aggregate component states into an overall state:
    the overall status is the worst status among all components.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

    @property
    def severity(self) -> int:
        """Numeric severity where higher is worse (used for aggregation)."""
        return _SEVERITY[self]


_SEVERITY: dict[HealthStatus, int] = {
    HealthStatus.HEALTHY: 0,
    HealthStatus.DEGRADED: 1,
    HealthStatus.UNHEALTHY: 2,
}


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    """Health of a single dependency (e.g. database, cache)."""

    name: str
    status: HealthStatus
    detail: str | None = None
    latency_ms: float | None = None


@dataclass(frozen=True, slots=True)
class SystemHealth:
    """Aggregate health of the service and all its components."""

    status: HealthStatus
    components: tuple[ComponentHealth, ...] = field(default_factory=tuple)

    @classmethod
    def from_components(cls, components: tuple[ComponentHealth, ...]) -> SystemHealth:
        """Derive overall status as the worst component status.

        With no components the system is considered healthy (liveness only).
        """
        if not components:
            return cls(status=HealthStatus.HEALTHY, components=())
        worst = max(components, key=lambda c: c.status.severity).status
        return cls(status=worst, components=components)

    @property
    def is_ready(self) -> bool:
        """True when the service can accept traffic (not fully unhealthy)."""
        return self.status is not HealthStatus.UNHEALTHY
