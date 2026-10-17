"""Infrastructure DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SubmitJobRequestDTO:
    job_type: str
    name: str
    dataset_id: str | None
    version_id: str | None
    resource_type: str | None
    resource_id: str | None
    configuration: dict[str, Any]


@dataclass(frozen=True, slots=True)
class JobSnapshotDTO:
    id: str
    job_type: str
    status: str
    name: str
    progress: int
    error_message: str | None
    retry_count: int
    logs: tuple[str, ...]
    queued_at: str
    started_at: str | None
    completed_at: str | None
    estimated_duration_ms: int | None
    duration_ms: int | None


@dataclass(frozen=True, slots=True)
class InfrastructureMetricsDTO:
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


@dataclass(frozen=True, slots=True)
class CacheEntryDTO:
    key: str
    namespace: str
    ttl_seconds: int
    version_key: str | None
