"""Dataset lifecycle use cases."""

from __future__ import annotations

from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.dataset import (
    ColumnMetadataDTO,
    DatasetDTO,
    DatasetPreviewDTO,
    DatasetVersionDTO,
    UploadResultDTO,
    ValidationReportDTO,
)
from app.application.services.datasets.ingestion_pipeline import DatasetIngestionPipeline, IngestionInput
from app.domain.entities.column_metadata import ColumnMetadata
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.validation_report import ValidationReport
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.schema_snapshot_repository import SchemaSnapshotRepository
from app.domain.repositories.validation_report_repository import ValidationReportRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.role import Permission
from app.domain.value_objects.tenant import TenantContext
from app.shared.exceptions import NotFoundError


class _ProjectAccessGuard:
    def __init__(
        self,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
    ) -> None:
        self._projects = projects
        self._workspaces = workspaces

    async def ensure_project_in_tenant(
        self, *, tenant: TenantContext, project_id: UUID
    ) -> None:
        workspace_id = await self._projects.get_workspace_id(project_id)
        if workspace_id is None:
            raise NotFoundError("Project not found.")
        workspace = await self._workspaces.get_by_id(
            workspace_id=workspace_id,
            organization_id=tenant.organization_id,
        )
        if workspace is None:
            raise NotFoundError("Project not found.")


class UploadDatasetUseCase:
    def __init__(
        self,
        pipeline: DatasetIngestionPipeline,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._pipeline = pipeline
        self._guard = _ProjectAccessGuard(projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        project_id: UUID,
        filename: str,
        content_type: str | None,
        data: bytes,
        name: str | None = None,
        description: str | None = None,
    ) -> UploadResultDTO:
        self._authorization.require_permission(tenant.role, Permission.DATASET_CREATE)
        await self._guard.ensure_project_in_tenant(tenant=tenant, project_id=project_id)
        return await self._pipeline.ingest(
            IngestionInput(
                tenant=tenant,
                project_id=project_id,
                organization_id=tenant.organization_id,
                filename=filename,
                content_type=content_type,
                data=data,
                name=name,
                description=description,
            )
        )


class UploadDatasetVersionUseCase:
    def __init__(
        self,
        pipeline: DatasetIngestionPipeline,
        datasets: DatasetRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._pipeline = pipeline
        self._datasets = datasets
        self._guard = _ProjectAccessGuard(projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        filename: str,
        content_type: str | None,
        data: bytes,
    ) -> UploadResultDTO:
        self._authorization.require_permission(tenant.role, Permission.DATASET_UPDATE)
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")
        await self._guard.ensure_project_in_tenant(tenant=tenant, project_id=dataset.project_id)
        return await self._pipeline.ingest(
            IngestionInput(
                tenant=tenant,
                project_id=dataset.project_id,
                organization_id=tenant.organization_id,
                filename=filename,
                content_type=content_type,
                data=data,
                dataset=dataset,
            )
        )


class ListDatasetsUseCase:
    def __init__(
        self,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._guard = _ProjectAccessGuard(projects, workspaces)
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, project_id: UUID) -> list[DatasetDTO]:
        self._authorization.require_permission(tenant.role, Permission.DATASET_READ)
        await self._guard.ensure_project_in_tenant(tenant=tenant, project_id=project_id)
        rows = await self._datasets.list_for_project(
            project_id=project_id, organization_id=tenant.organization_id
        )
        results: list[DatasetDTO] = []
        for row in rows:
            latest = None
            if row.current_version_id:
                version = await self._versions.get_by_id(version_id=row.current_version_id)
                latest = _to_version_dto(version) if version else None
            results.append(_to_dataset_dto(row, latest))
        return results


class GetDatasetUseCase:
    def __init__(
        self,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._guard = _ProjectAccessGuard(projects, workspaces)
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, dataset_id: UUID) -> DatasetDTO:
        self._authorization.require_permission(tenant.role, Permission.DATASET_READ)
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")
        await self._guard.ensure_project_in_tenant(tenant=tenant, project_id=dataset.project_id)
        latest = None
        if dataset.current_version_id:
            version = await self._versions.get_by_id(version_id=dataset.current_version_id)
            latest = _to_version_dto(version) if version else None
        return _to_dataset_dto(dataset, latest)


class ListDatasetVersionsUseCase:
    def __init__(
        self,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._guard = _ProjectAccessGuard(projects, workspaces)
        self._authorization = authorization

    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID
    ) -> list[DatasetVersionDTO]:
        self._authorization.require_permission(tenant.role, Permission.DATASET_READ)
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")
        await self._guard.ensure_project_in_tenant(tenant=tenant, project_id=dataset.project_id)
        rows = await self._versions.list_for_dataset(dataset_id=dataset_id)
        return [_to_version_dto(row) for row in rows]


class GetDatasetPreviewUseCase:
    def __init__(
        self,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        schemas: SchemaSnapshotRepository,
        validations: ValidationReportRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
        settings: object,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._schemas = schemas
        self._validations = validations
        self._guard = _ProjectAccessGuard(projects, workspaces)
        self._authorization = authorization
        self._settings = settings

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
    ) -> DatasetPreviewDTO:
        from app.core.config import Settings
        from app.infrastructure.processing.tabular_processor import TabularProcessor
        from app.infrastructure.storage.local_storage import LocalStorageProvider

        assert isinstance(self._settings, Settings)

        self._authorization.require_permission(tenant.role, Permission.DATASET_READ)
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")
        await self._guard.ensure_project_in_tenant(tenant=tenant, project_id=dataset.project_id)

        target_version_id = version_id or dataset.current_version_id
        if target_version_id is None:
            raise NotFoundError("Dataset has no versions to preview.")

        version = await self._versions.get_by_id(version_id=target_version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found.")

        schema = await self._schemas.get_by_version(version_id=version.id)
        validation = await self._validations.get_by_version(version_id=version.id)

        storage = LocalStorageProvider(self._settings)
        processor = TabularProcessor(self._settings)
        import tempfile
        from pathlib import Path

        data = await storage.read(key=version.storage_key)
        with tempfile.NamedTemporaryFile(
            suffix=f".{version.source_format.value}", delete=False
        ) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        try:
            profile = processor.profile_file(path=tmp_path, source_format=version.source_format)
        finally:
            tmp_path.unlink(missing_ok=True)

        columns = schema.columns if schema else profile.columns
        return DatasetPreviewDTO(
            dataset_id=dataset_id,
            version_id=version.id,
            version_number=version.version_number,
            row_count=version.row_count,
            column_count=version.column_count,
            columns=tuple(_to_column_dto(col) for col in columns),
            rows=profile.preview_rows[: self._settings.preview_row_limit],
            validation=_to_validation_dto(validation) if validation else None,
        )


class DeleteDatasetUseCase:
    def __init__(
        self,
        datasets: DatasetRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._datasets = datasets
        self._guard = _ProjectAccessGuard(projects, workspaces)
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, dataset_id: UUID) -> None:
        self._authorization.require_permission(tenant.role, Permission.DATASET_DELETE)
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")
        await self._guard.ensure_project_in_tenant(tenant=tenant, project_id=dataset.project_id)
        await self._datasets.soft_delete(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )


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


def _to_dataset_dto(dataset: Dataset, latest: DatasetVersionDTO | None) -> DatasetDTO:
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
        latest_version=latest,
    )


def _to_column_dto(column: ColumnMetadata) -> ColumnMetadataDTO:
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


def _to_validation_dto(report: ValidationReport) -> ValidationReportDTO:
    return ValidationReportDTO(
        status=report.status,
        checks=report.checks,
        errors=report.errors,
        warnings=report.warnings,
    )
