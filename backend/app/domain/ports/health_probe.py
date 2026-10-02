"""Port for probing the health of an external dependency.

Each infrastructure dependency (PostgreSQL, Redis, and future ones) provides a
concrete :class:`HealthProbe`. The application layer depends only on this
abstraction, so new dependencies can be health-checked without modifying the
use-case that aggregates them (Open/Closed Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.health import ComponentHealth


class HealthProbe(ABC):
    """Abstract probe that reports the health of one component."""

    @property
    @abstractmethod
    def component_name(self) -> str:
        """Stable identifier for the probed component (e.g. ``"postgres"``)."""
        raise NotImplementedError

    @abstractmethod
    async def check(self) -> ComponentHealth:
        """Probe the dependency and return its current health.

        Implementations must never raise for an *expected* failure (e.g. the
        dependency being down); instead they return a ``ComponentHealth`` with
        an ``UNHEALTHY``/``DEGRADED`` status. This keeps the aggregation logic
        simple and total.
        """
        raise NotImplementedError
