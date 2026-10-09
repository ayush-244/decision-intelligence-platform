"""AnalyticsJob — persisted background work unit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.infrastructure import JobStatus, JobType


@dataclass(frozen=True, slots=True)
class AnalyticsJob:
    id: UUID
    organization_id: UUID
    created_by: UUID | None
    job_type: JobType
    status: JobStatus
    dataset_id: UUID | None
    version_id: UUID | None
    resource_type: str | None
    resource_id: UUID | None
    name: str
    configuration: dict[str, Any]
    result: dict[str, Any]
    progress: int
    error_message: str | None
    retry_count: int
    max_retries: int
    logs: tuple[str, ...]
    estimated_duration_ms: int | None
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
