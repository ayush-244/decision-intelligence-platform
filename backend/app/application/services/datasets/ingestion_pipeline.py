"""Modular dataset ingestion pipeline."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from app.application.dto.dataset import (
    ColumnMetadataDTO,
    DatasetDTO,
    DatasetVersionDTO,
    UploadJobDTO,
    UploadResultDTO,
    ValidationReportDTO,
)
from app.application.services.datasets.file_validator import UploadFileValidator
from app.core.config import Settings
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_file import DatasetFile
from app.domain.entities.dataset_statistics import DatasetStatistics
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.schema_snapshot import SchemaSnapshot
from app.domain.entities.upload_job import UploadJob
from app.domain.entities.validation_report import ValidationReport
from app.domain.ports.storage_provider import StorageProvider
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.dataset_file_repository import DatasetFileRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_statistics_repository import DatasetStatisticsRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.schema_snapshot_repository import SchemaSnapshotRepository
from app.domain.repositories.upload_job_repository import UploadJobRepository
from app.domain.repositories.validation_report_repository import ValidationReportRepository
from app.domain.value_objects.dataset_status import UploadJobStatus, ValidationStatus
from app.domain.value_objects.tenant import TenantContext
from app.infrastructure.processing.tabular_processor import TabularProcessor
from app.shared.exceptions import BusinessValidationError, ConflictError
from app.shared.utils.datetime import utc_now
from app.shared.utils.file_hash import hash_bytes
from app.shared.utils.filename import sanitize_filename, unique_storage_filename


@dataclass(frozen=True, slots=True)
class IngestionInput:
    tenant: TenantContext
    project_id: UUID
    organization_id: UUID
    filename: str
    content_type: str | None
    data: bytes
    dataset: Dataset | None = None
    name: str | None = None
    description: str | None = None


class DatasetIngestionPipeline:
    """Orchestrate validate → store → profile → persist for each upload."""

    def __init__(
        self,
        settings: Settings,
        storage: StorageProvider,
        validator: UploadFileValidator,
        processor: TabularProcessor,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        files: DatasetFileRepository,
        jobs: UploadJobRepository,
        schemas: SchemaSnapshotRepository,
        validations: ValidationReportRepository,
        statistics: DatasetStatisticsRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._settings = settings
        self._storage = storage
        self._validator = validator
        self._processor = processor
        self._datasets = datasets
        self._versions = versions
        self._files = files
        self._jobs = jobs
        self._schemas = schemas
        self._validations = validations
        self._statistics = statistics
        self._audit_logs = audit_logs

    async def ingest(self, payload: IngestionInput) -> UploadResultDTO:
        validation = self._validator.validate(
            filename=payload.filename,
            content_type=payload.content_type,
            data=payload.data,
        )
        file_hash = hash_bytes(payload.data)

        duplicate = await self._versions.find_by_file_hash(
            organization_id=payload.organization_id,
            file_hash=file_hash,
        )
        warnings = list(validation.warnings)
        if duplicate is not None:
            warnings.append(
                "An identical file was previously uploaded in this organization."
            )

        dataset = payload.dataset
        if dataset is None:
            name = payload.name or Path(payload.filename).stem
            if await self._datasets.exists_by_name(project_id=payload.project_id, name=name):
                raise ConflictError("A dataset with this name already exists in the project.")
            from app.shared.utils.slug import slugify

            dataset = await self._datasets.create(
                project_id=payload.project_id,
                organization_id=payload.organization_id,
                name=name,
                slug=slugify(name),
                description=payload.description,
                created_by=payload.tenant.user_id,
            )

        job = await self._jobs.create(
            UploadJob(
                id=uuid4(),
                dataset_id=dataset.id,
                version_id=None,
                organization_id=payload.organization_id,
                project_id=payload.project_id,
                created_by=payload.tenant.user_id,
                status=UploadJobStatus.VALIDATING,
                error_message=None,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
        )

        try:
            version_number = await self._versions.next_version_number(dataset_id=dataset.id)
            sanitized = unique_storage_filename(payload.filename)
            storage_key = self._build_storage_key(
                organization_id=payload.organization_id,
                project_id=payload.project_id,
                dataset_id=dataset.id,
                version_number=version_number,
                filename=sanitized,
            )

            await self._jobs.update_status(job_id=job.id, status=UploadJobStatus.PROCESSING)
            await self._storage.store(
                key=storage_key,
                data=payload.data,
                content_type=payload.content_type or "application/octet-stream",
            )

            profile = await self._profile_stored_file(
                storage_key=storage_key,
                source_format=validation.format,
            )

            version_id = uuid4()
            version = DatasetVersion(
                id=version_id,
                dataset_id=dataset.id,
                version_number=version_number,
                uploaded_by=payload.tenant.user_id,
                source_format=validation.format,
                file_hash=file_hash,
                schema_hash=profile.schema_hash,
                row_count=profile.row_count,
                column_count=len(profile.columns),
                file_size_bytes=validation.size_bytes,
                storage_key=storage_key,
                validation_status=ValidationStatus.PASSED,
                created_at=utc_now(),
            )
            await self._versions.create(version)

            await self._files.create(
                DatasetFile(
                    id=uuid4(),
                    version_id=version_id,
                    original_filename=payload.filename,
                    sanitized_filename=sanitize_filename(payload.filename),
                    mime_type=payload.content_type or "application/octet-stream",
                    file_size_bytes=validation.size_bytes,
                    file_hash=file_hash,
                    storage_key=storage_key,
                    created_at=utc_now(),
                )
            )

            await self._schemas.create(
                SchemaSnapshot(
                    id=uuid4(),
                    version_id=version_id,
                    schema_hash=profile.schema_hash,
                    columns=profile.columns,
                    created_at=utc_now(),
                )
            )

            report = ValidationReport(
                id=uuid4(),
                version_id=version_id,
                status=ValidationStatus.PASSED if not warnings else ValidationStatus.WARNING,
                checks=validation.checks,
                errors=(),
                warnings=tuple(warnings),
                created_at=utc_now(),
            )
            await self._validations.create(report)

            await self._statistics.create(
                DatasetStatistics(
                    id=uuid4(),
                    version_id=version_id,
                    metrics={"profiled": True},
                    created_at=utc_now(),
                )
            )

            await self._datasets.update_current_version(
                dataset_id=dataset.id, version_id=version_id
            )
            await self._jobs.update_status(
                job_id=job.id,
                status=UploadJobStatus.COMPLETED,
                version_id=version_id,
            )

            await self._audit_logs.append(
                action="dataset.version.created",
                resource_type="dataset_version",
                user_id=payload.tenant.user_id,
                organization_id=payload.organization_id,
                resource_id=version_id,
                metadata={
                    "dataset_id": str(dataset.id),
                    "version_number": version_number,
                    "format": validation.format.value,
                },
            )

            dataset = await self._datasets.get_by_id(
                dataset_id=dataset.id, organization_id=payload.organization_id
            )
            assert dataset is not None

            return UploadResultDTO(
                dataset=_to_dataset_dto(dataset, version),
                version=_to_version_dto(version),
                job=UploadJobDTO(
                    id=job.id,
                    dataset_id=dataset.id,
                    status=UploadJobStatus.COMPLETED,
                    error_message=None,
                ),
                validation=ValidationReportDTO(
                    status=report.status,
                    checks=report.checks,
                    errors=report.errors,
                    warnings=report.warnings,
                ),
                preview_rows=profile.preview_rows,
            )
        except Exception as exc:
            await self._jobs.update_status(
                job_id=job.id,
                status=UploadJobStatus.FAILED,
                error_message=str(exc),
            )
            if isinstance(exc, BusinessValidationError | ConflictError):
                raise
            raise BusinessValidationError(
                "Failed to process dataset. The file may be corrupted or malformed."
            ) from exc

    def _build_storage_key(
        self,
        *,
        organization_id: UUID,
        project_id: UUID,
        dataset_id: UUID,
        version_number: int,
        filename: str,
    ) -> str:
        return (
            f"{organization_id}/{project_id}/{dataset_id}/v{version_number}/{filename}"
        )

    async def _profile_stored_file(self, *, storage_key: str, source_format: object) -> object:
        data = await self._storage.read(key=storage_key)
        with tempfile.NamedTemporaryFile(
            suffix=f".{source_format.value}", delete=False
        ) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        try:
            return self._processor.profile_file(path=tmp_path, source_format=source_format)  # type: ignore[arg-type]
        finally:
            tmp_path.unlink(missing_ok=True)


def _to_version_dto(version: DatasetVersion) -> DatasetVersionDTO:
    return DatasetVersionDTO(
        id=version.id,
        dataset_id=version.dataset_id,
        version_number=version.version_number,
        uploaded_by=version.uploaded_by,
        source_format=version.source_format,
        file_hash=version.file_hash,
        schema_hash=version.schema_hash,
        row_count=version.row_count,
        column_count=version.column_count,
        file_size_bytes=version.file_size_bytes,
        validation_status=version.validation_status,
        created_at=version.created_at,
    )


def _to_dataset_dto(dataset: Dataset, version: DatasetVersion) -> DatasetDTO:
    return DatasetDTO(
        id=dataset.id,
        project_id=dataset.project_id,
        organization_id=dataset.organization_id,
        name=dataset.name,
        slug=dataset.slug,
        description=dataset.description,
        created_by=dataset.created_by,
        current_version_id=dataset.current_version_id,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at,
        latest_version=_to_version_dto(version),
    )


def _column_dto(column: object) -> ColumnMetadataDTO:
    from app.domain.entities.column_metadata import ColumnMetadata

    assert isinstance(column, ColumnMetadata)
    return ColumnMetadataDTO(
        name=column.name,
        position=column.position,
        semantic_type=column.semantic_type,
        storage_type=column.storage_type,
        null_percentage=column.null_percentage,
        distinct_count=column.distinct_count,
        example_values=column.example_values,
        type_confidence=column.type_confidence,
    )
