"""Statistics use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.statistics import AnalysisRequestDTO, VariableSpecDTO
from app.application.services.intelligence.frame_loader import DatasetFrameLoader
from app.application.services.statistics.engine import StatisticsEngine
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.statistical_analysis import StatisticalAnalysisRun
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.role import Permission
from app.domain.value_objects.statistics import AnalysisRunStatus, StatisticalTestType
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


class RunStatisticalAnalysisUseCase:
    def __init__(
        self,
        engine: StatisticsEngine,
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
        goal: str,
        research_question: str,
        variables: list[dict[str, str]],
        version_id: UUID | None = None,
        test_type: str | None = None,
        confidence_level: float = 0.95,
        reference_value: float | None = None,
    ) -> StatisticalAnalysisRun:
        self._authorization.require_permission(tenant.role, Permission.STATISTICS_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        var_specs = tuple(VariableSpecDTO(name=v["name"], role=v["role"]) for v in variables)
        request = AnalysisRequestDTO(
            dataset_id=dataset_id,
            version_id=version.id,
            goal=goal,
            research_question=research_question,
            variables=var_specs,
            test_type=StatisticalTestType(test_type) if test_type else None,
            confidence_level=confidence_level,
            reference_value=reference_value,
        )
        return await self._engine.analyze(
            dataset=dataset,
            version=version,
            request=request,
            created_by=tenant.user_id,
        )


class GetStatisticalAnalysisUseCase:
    def __init__(
        self,
        analyses: StatisticalAnalysisRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._analyses = analyses
        self._authorization = authorization

    async def execute(
        self, *, tenant: TenantContext, analysis_id: UUID
    ) -> StatisticalAnalysisRun:
        self._authorization.require_permission(tenant.role, Permission.STATISTICS_READ)
        run = await self._analyses.get_by_id(
            analysis_id=analysis_id, organization_id=tenant.organization_id
        )
        if run is None:
            raise NotFoundError("Analysis not found.")
        if run.status is AnalysisRunStatus.FAILED:
            raise BusinessValidationError(
                run.error_message or "Analysis failed.",
                code="analysis_failed",
            )
        return run


class ListStatisticalAnalysisHistoryUseCase:
    def __init__(
        self,
        analyses: StatisticalAnalysisRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._analyses = analyses
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
        limit: int = 50,
    ) -> list[StatisticalAnalysisRun]:
        self._authorization.require_permission(tenant.role, Permission.STATISTICS_READ)
        if version_id:
            await self._guard.resolve_version(
                tenant=tenant, dataset_id=dataset_id, version_id=version_id
            )
            return await self._analyses.list_for_version(
                version_id=version_id, organization_id=tenant.organization_id, limit=limit
            )
        await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=None
        )
        return await self._analyses.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=limit
        )


class GetStatisticalRecommendationsUseCase:
    def __init__(
        self,
        engine: StatisticsEngine,
        frame_loader: DatasetFrameLoader,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._frame_loader = frame_loader
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        goal: str,
        variables: list[dict[str, str]],
        version_id: UUID | None = None,
    ) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.STATISTICS_READ)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        sampled = await self._frame_loader.load(version=version)
        var_specs = tuple(VariableSpecDTO(name=v["name"], role=v["role"]) for v in variables)
        request = AnalysisRequestDTO(
            dataset_id=dataset_id,
            version_id=version.id,
            goal=goal,
            research_question="",
            variables=var_specs,
        )
        recommendation = await self._engine.recommend(request=request, frame=sampled.frame)
        from app.application.services.statistics.serialization import to_jsonable

        return to_jsonable(recommendation)
