"""Dataset wire and application DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.column_type import ColumnSemanticType
from app.domain.value_objects.data_source import DataSourceFormat
from app.domain.value_objects.dataset_status import UploadJobStatus, ValidationStatus


@dataclass(frozen=True, slots=True)
class ColumnMetadataDTO:
    name: str
    position: int
    semantic_type: ColumnSemanticType
    storage_type: str
    null_percentage: float
    distinct_count: int | None
    example_values: tuple[str, ...]
    type_confidence: float


@dataclass(frozen=True, slots=True)
class DatasetVersionDTO:
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
    validation_status: ValidationStatus
    created_at: datetime


@dataclass(frozen=True, slots=True)
class DatasetDTO:
    id: UUID
    project_id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    created_by: UUID
    current_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    latest_version: DatasetVersionDTO | None = None


@dataclass(frozen=True, slots=True)
class UploadJobDTO:
    id: UUID
    dataset_id: UUID
    status: UploadJobStatus
    error_message: str | None


@dataclass(frozen=True, slots=True)
class ValidationReportDTO:
    status: ValidationStatus
    checks: dict[str, Any]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DatasetPreviewDTO:
    dataset_id: UUID
    version_id: UUID
    version_number: int
    row_count: int
    column_count: int
    columns: tuple[ColumnMetadataDTO, ...]
    rows: list[dict[str, Any]]
    validation: ValidationReportDTO | None


@dataclass(frozen=True, slots=True)
class UploadResultDTO:
    dataset: DatasetDTO
    version: DatasetVersionDTO
    job: UploadJobDTO
    validation: ValidationReportDTO
    preview_rows: list[dict[str, Any]]
