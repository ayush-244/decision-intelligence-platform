"""Dataset intelligence use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.services.intelligence.engine import IntelligenceEngine
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.intelligence_report import IntelligenceReport
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.intelligence_status import IntelligenceReportStatus
from app.domain.value_objects.role import Permission
from app.domain.value_objects.tenant import TenantContext
from app.shared.exceptions import BusinessValidationError, NotFoundError


class _DatasetAccessGuard:
    def __init__(
        self,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
    ) -> None:
        self._datasets = datasets
        self._versions = versions
        self._projects = projects
        self._workspaces = workspaces

    async def resolve_version(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None,
    ) -> tuple[Dataset, DatasetVersion]:
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")

        workspace_id = await self._projects.get_workspace_id(dataset.project_id)
        if workspace_id is None:
            raise NotFoundError("Dataset not found.")
        workspace = await self._workspaces.get_by_id(
            workspace_id=workspace_id, organization_id=tenant.organization_id
        )
        if workspace is None:
            raise NotFoundError("Dataset not found.")

        target_version_id = version_id or dataset.current_version_id
        if target_version_id is None:
            raise NotFoundError("Dataset has no versions to analyze.")

        version = await self._versions.get_by_id(version_id=target_version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found.")
        return dataset, version


class AnalyzeDatasetIntelligenceUseCase:
    def __init__(
        self,
        engine: IntelligenceEngine,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
    ) -> IntelligenceReport:
        self._authorization.require_permission(tenant.role, Permission.DATASET_UPDATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return await self._engine.analyze(dataset=dataset, version=version)


class _GetReportBase:
    def __init__(
        self,
        reports: IntelligenceReportRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._reports = reports
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def _get_report(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None,
    ) -> IntelligenceReport:
        self._authorization.require_permission(tenant.role, Permission.DATASET_READ)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        report = await self._reports.get_by_version(version_id=version.id)
        if report is None:
            raise NotFoundError(
                "Intelligence report not found. Run analysis first.",
                code="intelligence_not_found",
            )
        if report.status is IntelligenceReportStatus.FAILED:
            raise BusinessValidationError(
                report.error_message or "Intelligence analysis failed.",
                code="intelligence_failed",
            )
        if report.status is not IntelligenceReportStatus.COMPLETED:
            raise BusinessValidationError(
                "Intelligence report is not ready yet.",
                code="intelligence_pending",
            )
        return report


class GetDatasetIntelligenceUseCase(_GetReportBase):
    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
    ) -> dict[str, Any]:
        report = await self._get_report(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return {
            "status": report.status.value,
            "quality_score": report.quality_score,
            "health_score": report.health_score,
            "rows_sampled": report.rows_sampled,
            "total_rows": report.total_rows,
            "computed_at": report.computed_at.isoformat() if report.computed_at else None,
            **report.report,
        }


class GetDatasetQualityUseCase(_GetReportBase):
    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID, version_id: UUID | None = None
    ) -> dict[str, Any]:
        report = await self._get_report(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        payload = IntelligenceEngine.section(report, "data_quality")
        return payload if isinstance(payload, dict) else {}


class GetDatasetColumnsIntelligenceUseCase(_GetReportBase):
    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID, version_id: UUID | None = None
    ) -> dict[str, Any]:
        report = await self._get_report(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        columns = IntelligenceEngine.section(report, "columns")
        return {"columns": columns}


class GetDatasetCorrelationsUseCase(_GetReportBase):
    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID, version_id: UUID | None = None
    ) -> dict[str, Any]:
        report = await self._get_report(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        payload = IntelligenceEngine.section(report, "correlations")
        return payload if isinstance(payload, dict) else {}


class GetDatasetOutliersUseCase(_GetReportBase):
    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID, version_id: UUID | None = None
    ) -> dict[str, Any]:
        report = await self._get_report(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        payload = IntelligenceEngine.section(report, "outliers")
        return payload if isinstance(payload, dict) else {}


class GetDatasetMissingUseCase(_GetReportBase):
    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID, version_id: UUID | None = None
    ) -> dict[str, Any]:
        report = await self._get_report(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        payload = IntelligenceEngine.section(report, "missing_data")
        return payload if isinstance(payload, dict) else {}


class GetDatasetIntelligenceSummaryUseCase(_GetReportBase):
    async def execute(
        self, *, tenant: TenantContext, dataset_id: UUID, version_id: UUID | None = None
    ) -> dict[str, Any]:
        report = await self._get_report(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return {
            "overview": IntelligenceEngine.section(report, "overview"),
            "data_health": IntelligenceEngine.section(report, "data_health"),
            "analytical_readiness": IntelligenceEngine.section(report, "analytical_readiness"),
            "recommendations": IntelligenceEngine.section(report, "recommendations"),
            "quality_score": report.quality_score,
            "health_score": report.health_score,
        }
