"""Infrastructure API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.application.dto.infrastructure import JobSnapshotDTO


class SubmitJobRequest(BaseModel):
    job_type: str
    name: str
    dataset_id: str | None = None
    version_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)


class JobSnapshotResponse(BaseModel):
    id: str
    job_type: str
    status: str
    name: str
    progress: int
    error_message: str | None
    retry_count: int
    logs: list[str]
    queued_at: str
    started_at: str | None
    completed_at: str | None
    estimated_duration_ms: int | None
    duration_ms: int | None

    @classmethod
    def from_dto(cls, dto: JobSnapshotDTO) -> JobSnapshotResponse:
        return cls(
            id=dto.id,
            job_type=dto.job_type,
            status=dto.status,
            name=dto.name,
            progress=dto.progress,
            error_message=dto.error_message,
            retry_count=dto.retry_count,
            logs=list(dto.logs),
            queued_at=dto.queued_at,
            started_at=dto.started_at,
            completed_at=dto.completed_at,
            estimated_duration_ms=dto.estimated_duration_ms,
            duration_ms=dto.duration_ms,
        )


class InfrastructureMetricsResponse(BaseModel):
    queue_depth: int
    jobs_queued: int
    jobs_running: int
    jobs_completed_24h: int
    jobs_failed_24h: int
    cache_hits: int
    cache_misses: int
    cache_keys: int
    avg_job_duration_ms: float | None
    slow_queries_detected: int


class InvalidateCacheRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
