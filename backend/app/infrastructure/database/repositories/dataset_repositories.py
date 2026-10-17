"""SQLAlchemy repository implementations for datasets."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_file import DatasetFile
from app.domain.entities.dataset_statistics import DatasetStatistics
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.intelligence_report import IntelligenceReport
from app.domain.entities.schema_snapshot import SchemaSnapshot
from app.domain.entities.upload_job import UploadJob
from app.domain.entities.validation_report import ValidationReport
from app.domain.repositories.dataset_file_repository import DatasetFileRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_statistics_repository import DatasetStatisticsRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.domain.repositories.schema_snapshot_repository import SchemaSnapshotRepository
from app.domain.repositories.upload_job_repository import UploadJobRepository
from app.domain.repositories.validation_report_repository import ValidationReportRepository
from app.domain.value_objects.dataset_status import UploadJobStatus
from app.infrastructure.database.mappers.dataset import (
    columns_to_json,
    to_dataset,
    to_dataset_file,
    to_dataset_statistics,
    to_dataset_version,
    to_schema_snapshot,
    to_upload_job,
    to_validation_report,
)
from app.infrastructure.database.mappers.intelligence import to_intelligence_report
from app.infrastructure.database.models.dataset import DatasetModel
from app.infrastructure.database.models.dataset_file import DatasetFileModel
from app.infrastructure.database.models.dataset_statistics import DatasetStatisticsModel
from app.infrastructure.database.models.dataset_version import DatasetVersionModel
from app.infrastructure.database.models.intelligence_report import IntelligenceReportModel
from app.infrastructure.database.models.schema_snapshot import SchemaSnapshotModel
from app.infrastructure.database.models.upload_job import UploadJobModel
from app.infrastructure.database.models.validation_report import ValidationReportModel


class SqlAlchemyDatasetRepository(DatasetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, dataset_id: UUID, organization_id: UUID) -> Dataset | None:
        result = await self._session.execute(
            select(DatasetModel).where(
                DatasetModel.id == dataset_id,
                DatasetModel.organization_id == organization_id,
                DatasetModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return to_dataset(model) if model else None

    async def list_for_project(
        self, *, project_id: UUID, organization_id: UUID
    ) -> list[Dataset]:
        result = await self._session.execute(
            select(DatasetModel)
            .where(
                DatasetModel.project_id == project_id,
                DatasetModel.organization_id == organization_id,
                DatasetModel.deleted_at.is_(None),
            )
            .order_by(DatasetModel.name)
        )
        return [to_dataset(row) for row in result.scalars().all()]

    async def create(
        self,
        *,
        project_id: UUID,
        organization_id: UUID,
        name: str,
        slug: str,
        description: str | None,
        created_by: UUID,
    ) -> Dataset:
        model = DatasetModel(
            project_id=project_id,
            organization_id=organization_id,
            name=name,
            slug=slug,
            description=description,
            created_by=created_by,
        )
        self._session.add(model)
        await self._session.flush()
        return to_dataset(model)

    async def update_current_version(self, *, dataset_id: UUID, version_id: UUID) -> None:
        await self._session.execute(
            update(DatasetModel)
            .where(DatasetModel.id == dataset_id)
            .values(current_version_id=version_id)
        )
        await self._session.flush()

    async def soft_delete(self, *, dataset_id: UUID, organization_id: UUID) -> None:
        result = await self._session.execute(
            select(DatasetModel).where(
                DatasetModel.id == dataset_id,
                DatasetModel.organization_id == organization_id,
                DatasetModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        if model is not None:
            model.deleted_at = datetime.now(UTC)
            await self._session.flush()

    async def exists_by_name(
        self, *, project_id: UUID, name: str, exclude_id: UUID | None = None
    ) -> bool:
        stmt = select(func.count()).select_from(DatasetModel).where(
            DatasetModel.project_id == project_id,
            func.lower(DatasetModel.name) == name.lower(),
            DatasetModel.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(DatasetModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one()) > 0


class SqlAlchemyDatasetVersionRepository(DatasetVersionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, version_id: UUID) -> DatasetVersion | None:
        result = await self._session.execute(
            select(DatasetVersionModel).where(DatasetVersionModel.id == version_id)
        )
        model = result.scalar_one_or_none()
        return to_dataset_version(model) if model else None

    async def list_for_dataset(self, *, dataset_id: UUID) -> list[DatasetVersion]:
        result = await self._session.execute(
            select(DatasetVersionModel)
            .where(DatasetVersionModel.dataset_id == dataset_id)
            .order_by(DatasetVersionModel.version_number.desc())
        )
        return [to_dataset_version(row) for row in result.scalars().all()]

    async def get_latest(self, *, dataset_id: UUID) -> DatasetVersion | None:
        result = await self._session.execute(
            select(DatasetVersionModel)
            .where(DatasetVersionModel.dataset_id == dataset_id)
            .order_by(DatasetVersionModel.version_number.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return to_dataset_version(model) if model else None

    async def next_version_number(self, *, dataset_id: UUID) -> int:
        result = await self._session.execute(
            select(func.max(DatasetVersionModel.version_number)).where(
                DatasetVersionModel.dataset_id == dataset_id
            )
        )
        current = result.scalar_one_or_none()
        return int(current or 0) + 1

    async def create(self, version: DatasetVersion) -> DatasetVersion:
        model = DatasetVersionModel(
            id=version.id,
            dataset_id=version.dataset_id,
            version_number=version.version_number,
            uploaded_by=version.uploaded_by,
            source_format=version.source_format.value,
            file_hash=version.file_hash,
            schema_hash=version.schema_hash,
            row_count=version.row_count,
            column_count=version.column_count,
            file_size_bytes=version.file_size_bytes,
            storage_key=version.storage_key,
            validation_status=version.validation_status.value,
        )
        self._session.add(model)
        await self._session.flush()
        return to_dataset_version(model)

    async def find_by_file_hash(
        self, *, organization_id: UUID, file_hash: str
    ) -> DatasetVersion | None:
        result = await self._session.execute(
            select(DatasetVersionModel)
            .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
            .where(
                DatasetModel.organization_id == organization_id,
                DatasetVersionModel.file_hash == file_hash,
            )
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return to_dataset_version(model) if model else None


class SqlAlchemyDatasetFileRepository(DatasetFileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, file: DatasetFile) -> DatasetFile:
        model = DatasetFileModel(
            id=file.id,
            version_id=file.version_id,
            original_filename=file.original_filename,
            sanitized_filename=file.sanitized_filename,
            mime_type=file.mime_type,
            file_size_bytes=file.file_size_bytes,
            file_hash=file.file_hash,
            storage_key=file.storage_key,
        )
        self._session.add(model)
        await self._session.flush()
        return to_dataset_file(model)

    async def get_by_version(self, *, version_id: UUID) -> DatasetFile | None:
        result = await self._session.execute(
            select(DatasetFileModel).where(DatasetFileModel.version_id == version_id)
        )
        model = result.scalar_one_or_none()
        return to_dataset_file(model) if model else None


class SqlAlchemyUploadJobRepository(UploadJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: UploadJob) -> UploadJob:
        model = UploadJobModel(
            id=job.id,
            dataset_id=job.dataset_id,
            version_id=job.version_id,
            organization_id=job.organization_id,
            project_id=job.project_id,
            created_by=job.created_by,
            status=job.status.value,
            error_message=job.error_message,
        )
        self._session.add(model)
        await self._session.flush()
        return to_upload_job(model)

    async def update_status(
        self,
        *,
        job_id: UUID,
        status: UploadJobStatus,
        version_id: UUID | None = None,
        error_message: str | None = None,
    ) -> None:
        values: dict[str, object] = {"status": status.value, "error_message": error_message}
        if version_id is not None:
            values["version_id"] = version_id
        await self._session.execute(
            update(UploadJobModel).where(UploadJobModel.id == job_id).values(**values)
        )
        await self._session.flush()

    async def get_by_id(self, *, job_id: UUID) -> UploadJob | None:
        result = await self._session.execute(
            select(UploadJobModel).where(UploadJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return to_upload_job(model) if model else None


class SqlAlchemySchemaSnapshotRepository(SchemaSnapshotRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, snapshot: SchemaSnapshot) -> SchemaSnapshot:
        model = SchemaSnapshotModel(
            id=snapshot.id,
            version_id=snapshot.version_id,
            schema_hash=snapshot.schema_hash,
            columns_json=columns_to_json(snapshot.columns),
        )
        self._session.add(model)
        await self._session.flush()
        return to_schema_snapshot(model)

    async def get_by_version(self, *, version_id: UUID) -> SchemaSnapshot | None:
        result = await self._session.execute(
            select(SchemaSnapshotModel).where(SchemaSnapshotModel.version_id == version_id)
        )
        model = result.scalar_one_or_none()
        return to_schema_snapshot(model) if model else None


class SqlAlchemyValidationReportRepository(ValidationReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, report: ValidationReport) -> ValidationReport:
        model = ValidationReportModel(
            id=report.id,
            version_id=report.version_id,
            status=report.status.value,
            checks_json=report.checks,
            errors_json=list(report.errors),
            warnings_json=list(report.warnings),
        )
        self._session.add(model)
        await self._session.flush()
        return to_validation_report(model)

    async def get_by_version(self, *, version_id: UUID) -> ValidationReport | None:
        result = await self._session.execute(
            select(ValidationReportModel).where(ValidationReportModel.version_id == version_id)
        )
        model = result.scalar_one_or_none()
        return to_validation_report(model) if model else None


class SqlAlchemyDatasetStatisticsRepository(DatasetStatisticsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, statistics: DatasetStatistics) -> DatasetStatistics:
        model = DatasetStatisticsModel(
            id=statistics.id,
            version_id=statistics.version_id,
            metrics_json=statistics.metrics,
        )
        self._session.add(model)
        await self._session.flush()
        return to_dataset_statistics(model)

    async def get_by_version(self, *, version_id: UUID) -> DatasetStatistics | None:
        result = await self._session.execute(
            select(DatasetStatisticsModel).where(DatasetStatisticsModel.version_id == version_id)
        )
        model = result.scalar_one_or_none()
        return to_dataset_statistics(model) if model else None


class SqlAlchemyIntelligenceReportRepository(IntelligenceReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_version(self, *, version_id: UUID) -> IntelligenceReport | None:
        result = await self._session.execute(
            select(IntelligenceReportModel).where(
                IntelligenceReportModel.version_id == version_id
            )
        )
        model = result.scalar_one_or_none()
        return to_intelligence_report(model) if model else None

    async def get_by_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, version_id: UUID | None = None
    ) -> IntelligenceReport | None:
        stmt = select(IntelligenceReportModel).where(
            IntelligenceReportModel.dataset_id == dataset_id,
            IntelligenceReportModel.organization_id == organization_id,
        )
        if version_id is not None:
            stmt = stmt.where(IntelligenceReportModel.version_id == version_id)
        result = await self._session.execute(stmt.order_by(IntelligenceReportModel.created_at.desc()))
        model = result.scalars().first()
        return to_intelligence_report(model) if model else None

    async def upsert(self, report: IntelligenceReport) -> IntelligenceReport:
        result = await self._session.execute(
            select(IntelligenceReportModel).where(
                IntelligenceReportModel.version_id == report.version_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            model = IntelligenceReportModel(
                id=report.id,
                dataset_id=report.dataset_id,
                version_id=report.version_id,
                organization_id=report.organization_id,
                status=report.status.value,
                quality_score=report.quality_score,
                health_score=report.health_score,
                rows_sampled=report.rows_sampled,
                total_rows=report.total_rows,
                report_json=report.report,
                error_message=report.error_message,
                computed_at=report.computed_at,
            )
            self._session.add(model)
        else:
            existing.status = report.status.value
            existing.quality_score = report.quality_score
            existing.health_score = report.health_score
            existing.rows_sampled = report.rows_sampled
            existing.total_rows = report.total_rows
            existing.report_json = report.report
            existing.error_message = report.error_message
            existing.computed_at = report.computed_at
            model = existing
        await self._session.flush()
        return to_intelligence_report(model)

    async def delete_for_version(self, *, version_id: UUID) -> None:
        result = await self._session.execute(
            select(IntelligenceReportModel).where(
                IntelligenceReportModel.version_id == version_id
            )
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
