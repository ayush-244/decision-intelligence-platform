"""Schemas for health/readiness endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.entities.health import HealthStatus, SystemHealth


class ComponentHealthResponse(BaseModel):
    """Health of a single dependency."""

    name: str = Field(examples=["postgres"])
    status: HealthStatus = Field(examples=[HealthStatus.HEALTHY])
    detail: str | None = None
    latency_ms: float | None = Field(default=None, examples=[1.23])


class HealthResponse(BaseModel):
    """Aggregate readiness of the service and its dependencies."""

    status: HealthStatus = Field(examples=[HealthStatus.HEALTHY])
    components: list[ComponentHealthResponse] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, system_health: SystemHealth) -> HealthResponse:
        """Map the domain :class:`SystemHealth` to the wire schema."""
        return cls(
            status=system_health.status,
            components=[
                ComponentHealthResponse(
                    name=component.name,
                    status=component.status,
                    detail=component.detail,
                    latency_ms=component.latency_ms,
                )
                for component in system_health.components
            ],
        )


class LivenessResponse(BaseModel):
    """Minimal liveness payload (process is up and serving)."""

    status: str = Field(default="ok", examples=["ok"])
