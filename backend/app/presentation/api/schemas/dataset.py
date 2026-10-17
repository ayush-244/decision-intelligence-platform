"""Dataset API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.dto.dataset import (
    ColumnMetadataDTO,
    DatasetDTO,
    DatasetPreviewDTO,
    DatasetVersionDTO,
    UploadResultDTO,
    ValidationReportDTO,
)
from app.domain.value_objects.column_type import ColumnSemanticType
from app.domain.value_objects.data_source import DataSourceFormat
from app.domain.value_objects.dataset_status import UploadJobStatus, ValidationStatus


class ColumnMetadataResponse(BaseModel):
    name: str
    position: int
    semantic_type: ColumnSemanticType
    storage_type: str
    null_percentage: float
    distinct_count: int | None
    example_values: list[str]
    type_confidence: float

    @classmethod
    def from_dto(cls, dto: ColumnMetadataDTO) -> ColumnMetadataResponse:
        return cls(
            name=dto.name,
            position=dto.position,
            semantic_type=dto.semantic_type,
            storage_type=dto.storage_type,
            null_percentage=dto.null_percentage,
            distinct_count=dto.distinct_count,
            example_values=list(dto.example_values),
            type_confidence=dto.type_confidence,
        )


class DatasetVersionResponse(BaseModel):
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

    @classmethod
    def from_dto(cls, dto: DatasetVersionDTO) -> DatasetVersionResponse:
        return cls(
            id=dto.id,
            dataset_id=dto.dataset_id,
            version_number=dto.version_number,
            uploaded_by=dto.uploaded_by,
            source_format=dto.source_format,
            file_hash=dto.file_hash,
            schema_hash=dto.schema_hash,
            row_count=dto.row_count,
            column_count=dto.column_count,
            file_size_bytes=dto.file_size_bytes,
            validation_status=dto.validation_status,
            created_at=dto.created_at,
        )


class DatasetResponse(BaseModel):
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
    latest_version: DatasetVersionResponse | None = None

    @classmethod
    def from_dto(cls, dto: DatasetDTO) -> DatasetResponse:
        return cls(
            id=dto.id,
            project_id=dto.project_id,
            organization_id=dto.organization_id,
            name=dto.name,
            slug=dto.slug,
            description=dto.description,
            created_by=dto.created_by,
            current_version_id=dto.current_version_id,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            latest_version=(
                DatasetVersionResponse.from_dto(dto.latest_version)
                if dto.latest_version
                else None
            ),
        )


class ValidationReportResponse(BaseModel):
    status: ValidationStatus
    checks: dict[str, Any]
    errors: list[str]
    warnings: list[str]

    @classmethod
    def from_dto(cls, dto: ValidationReportDTO) -> ValidationReportResponse:
        return cls(
            status=dto.status,
            checks=dto.checks,
            errors=list(dto.errors),
            warnings=list(dto.warnings),
        )


class UploadResultResponse(BaseModel):
    dataset: DatasetResponse
    version: DatasetVersionResponse
    job_id: UUID
    job_status: UploadJobStatus
    validation: ValidationReportResponse
    preview_rows: list[dict[str, Any]]

    @classmethod
    def from_dto(cls, dto: UploadResultDTO) -> UploadResultResponse:
        return cls(
            dataset=DatasetResponse.from_dto(dto.dataset),
            version=DatasetVersionResponse.from_dto(dto.version),
            job_id=dto.job.id,
            job_status=dto.job.status,
            validation=ValidationReportResponse.from_dto(dto.validation),
            preview_rows=dto.preview_rows,
        )


class DatasetPreviewResponse(BaseModel):
    dataset_id: UUID
    version_id: UUID
    version_number: int
    row_count: int
    column_count: int
    columns: list[ColumnMetadataResponse]
    rows: list[dict[str, Any]]
    validation: ValidationReportResponse | None = None

    @classmethod
    def from_dto(cls, dto: DatasetPreviewDTO) -> DatasetPreviewResponse:
        return cls(
            dataset_id=dto.dataset_id,
            version_id=dto.version_id,
            version_number=dto.version_number,
            row_count=dto.row_count,
            column_count=dto.column_count,
            columns=[ColumnMetadataResponse.from_dto(col) for col in dto.columns],
            rows=dto.rows,
            validation=(
                ValidationReportResponse.from_dto(dto.validation) if dto.validation else None
            ),
        )
