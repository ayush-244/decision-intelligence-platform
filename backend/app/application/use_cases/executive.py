"""Executive intelligence use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.executive import GenerateReportRequestDTO
from app.application.services.executive.dashboard import DashboardEngine
from app.application.services.executive.engine import ExecutiveReportEngine
from app.application.services.executive.export import ExportEngine
from app.application.services.executive.serialization import to_jsonable
from app.domain.entities.executive_report import ExecutiveReport
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.executive import ExecutiveReportStatus, ExportFormat
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
    ) -> tuple[Any, Any]:
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
            raise NotFoundError("Dataset has no versions.")
        version = await self._versions.get_by_id(version_id=target_version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found.")
        return dataset, version


class GenerateExecutiveReportUseCase:
    def __init__(
        self,
        engine: ExecutiveReportEngine,
        decisions: DecisionRunRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._decisions = decisions
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        decision_run_id: UUID,
        name: str,
        business_objective: str,
        version_id: UUID | None = None,
        include_technical_appendix: bool = False,
    ) -> ExecutiveReport:
        self._authorization.require_permission(tenant.role, Permission.REPORT_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        decision = await self._decisions.get_by_id(
            decision_id=decision_run_id, organization_id=tenant.organization_id
        )
        if decision is None:
            raise NotFoundError("Decision analysis not found.")
        request = GenerateReportRequestDTO(
            dataset_id=str(dataset_id),
            version_id=str(version.id),
            decision_run_id=str(decision_run_id),
            name=name,
            business_objective=business_objective,
            include_technical_appendix=include_technical_appendix,
        )
        return await self._engine.generate(
            dataset=dataset,
            version=version,
            decision=decision,
            request=request,
            created_by=tenant.user_id,
        )


class GetExecutiveReportUseCase:
    def __init__(
        self,
        reports: ExecutiveReportRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._reports = reports
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, report_id: UUID) -> ExecutiveReport:
        self._authorization.require_permission(tenant.role, Permission.REPORT_READ)
        report = await self._reports.get_by_id(
            report_id=report_id, organization_id=tenant.organization_id
        )
        if report is None:
            raise NotFoundError("Report not found.")
        if report.status is ExecutiveReportStatus.FAILED:
            raise BusinessValidationError(
                report.error_message or "Report generation failed.", code="report_failed"
            )
        return report


class ListExecutiveReportsUseCase:
    def __init__(
        self,
        reports: ExecutiveReportRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._reports = reports
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        limit: int = 50,
    ) -> list[ExecutiveReport]:
        self._authorization.require_permission(tenant.role, Permission.REPORT_READ)
        await self._guard.resolve_version(tenant=tenant, dataset_id=dataset_id, version_id=None)
        return await self._reports.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=limit
        )


class ExportExecutiveReportUseCase(GetExecutiveReportUseCase):
    def __init__(
        self,
        reports: ExecutiveReportRepository,
        authorization: AuthorizationService,
    ) -> None:
        super().__init__(reports, authorization)
        self._export = ExportEngine()

    async def execute_export(
        self,
        *,
        tenant: TenantContext,
        report_id: UUID,
        format: str,
    ) -> dict[str, str]:
        self._authorization.require_permission(tenant.role, Permission.REPORT_READ)
        report = await self.execute(tenant=tenant, report_id=report_id)
        export_format = ExportFormat(format)
        payload = {**report.result, "name": report.name}
        content, media_type, ext = self._export.export(report=payload, format=export_format)
        return {
            "content": content,
            "media_type": media_type,
            "filename": f"{report.name.replace(' ', '_')}.{ext}",
        }


class GetExecutiveDashboardUseCase:
    def __init__(
        self,
        decisions: DecisionRunRepository,
        reports: ExecutiveReportRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._decisions = decisions
        self._reports = reports
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization
        self._dashboard = DashboardEngine()

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
    ) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.REPORT_READ)
        await self._guard.resolve_version(tenant=tenant, dataset_id=dataset_id, version_id=None)
        decisions = await self._decisions.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=100
        )
        reports = await self._reports.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=100
        )
        snapshot = self._dashboard.build(decisions=decisions, reports=reports)
        return to_jsonable(snapshot)
