"""DatasetVersion — immutable analytical snapshot.

Each upload creates a new version. Versions are never overwritten. The schema
hash and file hash enable deduplication detection and audit trails.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_objects.data_source import DataSourceFormat
from app.domain.value_objects.dataset_status import ValidationStatus


@dataclass(frozen=True, slots=True)
class DatasetVersion:
    id: UUID
    dataset_id: UUID
    version_number: int
    uploaded_by: UUID
    source_format: DataSourceFormat
    file_hash: str
    schema_hash: str
    row_count: int
    column_count: int
    file_size_bytes: int
    storage_key: str
    validation_status: ValidationStatus
    created_at: datetime
