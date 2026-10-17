"""Map dataset ORM models to domain entities."""

from __future__ import annotations

from app.domain.entities.column_metadata import ColumnMetadata
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_file import DatasetFile
from app.domain.entities.dataset_statistics import DatasetStatistics
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.schema_snapshot import SchemaSnapshot
from app.domain.entities.upload_job import UploadJob
from app.domain.entities.validation_report import ValidationReport
from app.domain.value_objects.column_type import ColumnSemanticType
from app.domain.value_objects.data_source import DataSourceFormat
from app.domain.value_objects.dataset_status import UploadJobStatus, ValidationStatus
from app.infrastructure.database.models.dataset import DatasetModel
from app.infrastructure.database.models.dataset_file import DatasetFileModel
from app.infrastructure.database.models.dataset_statistics import DatasetStatisticsModel
from app.infrastructure.database.models.dataset_version import DatasetVersionModel
from app.infrastructure.database.models.schema_snapshot import SchemaSnapshotModel
from app.infrastructure.database.models.upload_job import UploadJobModel
from app.infrastructure.database.models.validation_report import ValidationReportModel


def to_dataset(model: DatasetModel) -> Dataset:
    return Dataset(
        id=model.id,
        project_id=model.project_id,
        organization_id=model.organization_id,
        name=model.name,
        slug=model.slug,
        description=model.description,
        created_by=model.created_by,
        current_version_id=model.current_version_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


def to_dataset_version(model: DatasetVersionModel) -> DatasetVersion:
    return DatasetVersion(
        id=model.id,
        dataset_id=model.dataset_id,
        version_number=model.version_number,
        uploaded_by=model.uploaded_by,
        source_format=DataSourceFormat(model.source_format),
        file_hash=model.file_hash,
        schema_hash=model.schema_hash,
        row_count=model.row_count,
        column_count=model.column_count,
        file_size_bytes=model.file_size_bytes,
        storage_key=model.storage_key,
        validation_status=ValidationStatus(model.validation_status),
        created_at=model.created_at,
    )


def to_dataset_file(model: DatasetFileModel) -> DatasetFile:
    return DatasetFile(
        id=model.id,
        version_id=model.version_id,
        original_filename=model.original_filename,
        sanitized_filename=model.sanitized_filename,
        mime_type=model.mime_type,
        file_size_bytes=model.file_size_bytes,
        file_hash=model.file_hash,
        storage_key=model.storage_key,
        created_at=model.created_at,
    )


def to_upload_job(model: UploadJobModel) -> UploadJob:
    return UploadJob(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        created_by=model.created_by,
        status=UploadJobStatus(model.status),
        error_message=model.error_message,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _column_from_json(data: dict[str, object]) -> ColumnMetadata:
    examples = data.get("example_values", [])
    if isinstance(examples, list):
        example_tuple = tuple(str(v) for v in examples[:5])
    else:
        example_tuple = ()
    return ColumnMetadata(
        name=str(data["name"]),
        position=int(data["position"]),
        semantic_type=ColumnSemanticType(str(data["semantic_type"])),
        storage_type=str(data["storage_type"]),
        null_percentage=float(data.get("null_percentage", 0.0)),
        distinct_count=int(data["distinct_count"]) if data.get("distinct_count") is not None else None,
        example_values=example_tuple,
        type_confidence=float(data.get("type_confidence", 1.0)),
    )


def columns_to_json(columns: tuple[ColumnMetadata, ...]) -> list[dict[str, object]]:
    return [
        {
            "name": col.name,
            "position": col.position,
            "semantic_type": col.semantic_type.value,
            "storage_type": col.storage_type,
            "null_percentage": col.null_percentage,
            "distinct_count": col.distinct_count,
            "example_values": list(col.example_values),
            "type_confidence": col.type_confidence,
        }
        for col in columns
    ]


def to_schema_snapshot(model: SchemaSnapshotModel) -> SchemaSnapshot:
    raw = model.columns_json or []
    columns = tuple(_column_from_json(item) for item in raw)
    return SchemaSnapshot(
        id=model.id,
        version_id=model.version_id,
        schema_hash=model.schema_hash,
        columns=columns,
        created_at=model.created_at,
    )


def to_validation_report(model: ValidationReportModel) -> ValidationReport:
    return ValidationReport(
        id=model.id,
        version_id=model.version_id,
        status=ValidationStatus(model.status),
        checks=dict(model.checks_json or {}),
        errors=tuple(model.errors_json or []),
        warnings=tuple(model.warnings_json or []),
        created_at=model.created_at,
    )


def to_dataset_statistics(model: DatasetStatisticsModel) -> DatasetStatistics:
    return DatasetStatistics(
        id=model.id,
        version_id=model.version_id,
        metrics=dict(model.metrics_json or {}),
        created_at=model.created_at,
    )
