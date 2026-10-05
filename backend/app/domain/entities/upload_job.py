"""UploadJob — tracks ingestion lifecycle for observability and future async workers.

Even synchronous uploads create a job record so background processing can be
enabled later without API changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_objects.dataset_status import UploadJobStatus


@dataclass(frozen=True, slots=True)
class UploadJob:
    id: UUID
    dataset_id: UUID
    version_id: UUID | None
    organization_id: UUID
    project_id: UUID
    created_by: UUID
    status: UploadJobStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime
