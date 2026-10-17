"""Causal inference use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.causal import CausalAnalysisRequestDTO
from app.application.services.causal.dag_manager import DAGManager
from app.application.services.causal.engine import CausalEngine
from app.application.services.causal.serialization import to_jsonable
from app.application.services.intelligence.frame_loader import DatasetFrameLoader
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.dag_version import DAGVersion
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.dag_version_repository import DAGVersionRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.causal import CausalEstimatorType, CausalRunStatus
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
            raise NotFoundError("Dataset has no versions to analyze.")
        version = await self._versions.get_by_id(version_id=target_version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found.")
        return dataset, version


class RunCausalAnalysisUseCase:
    def __init__(
        self,
        engine: CausalEngine,
        dags: DAGVersionRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._dags = dags
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        treatment: str,
        outcome: str,
        business_question: str,
        version_id: UUID | None = None,
        dag_id: UUID | None = None,
        estimator: str | None = None,
        confidence_level: float = 0.95,
        adjustment_set: list[str] | None = None,
        run_refutation: bool = True,
        run_sensitivity: bool = True,
    ) -> CausalAnalysisRun:
        self._authorization.require_permission(tenant.role, Permission.CAUSAL_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        dag: DAGVersion | None = None
        if dag_id:
            dag = await self._dags.get_by_id(dag_id=dag_id, organization_id=tenant.organization_id)
            if dag is None:
                raise NotFoundError("DAG not found.")
        request = CausalAnalysisRequestDTO(
            dataset_id=str(dataset_id),
            version_id=str(version.id),
            dag_id=str(dag_id) if dag_id else None,
            treatment=treatment,
            outcome=outcome,
            business_question=business_question,
            estimator=CausalEstimatorType(estimator) if estimator else None,
            confidence_level=confidence_level,
            adjustment_set=tuple(adjustment_set) if adjustment_set else None,
            run_refutation=run_refutation,
            run_sensitivity=run_sensitivity,
        )
        return await self._engine.analyze(
            dataset=dataset, version=version, request=request, created_by=tenant.user_id, dag=dag,
        )


class GetCausalAnalysisUseCase:
    def __init__(
        self,
        analyses: CausalAnalysisRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._analyses = analyses
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, analysis_id: UUID) -> CausalAnalysisRun:
        self._authorization.require_permission(tenant.role, Permission.CAUSAL_READ)
        run = await self._analyses.get_by_id(
            analysis_id=analysis_id, organization_id=tenant.organization_id
        )
        if run is None:
            raise NotFoundError("Causal analysis not found.")
        if run.status is CausalRunStatus.FAILED:
            raise BusinessValidationError(
                run.error_message or "Causal analysis failed.", code="causal_failed"
            )
        return run


class ListCausalAnalysisHistoryUseCase:
    def __init__(
        self,
        analyses: CausalAnalysisRepository,
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
    ) -> list[CausalAnalysisRun]:
        self._authorization.require_permission(tenant.role, Permission.CAUSAL_READ)
        if version_id:
            await self._guard.resolve_version(
                tenant=tenant, dataset_id=dataset_id, version_id=version_id
            )
            return await self._analyses.list_for_version(
                version_id=version_id, organization_id=tenant.organization_id, limit=limit
            )
        await self._guard.resolve_version(tenant=tenant, dataset_id=dataset_id, version_id=None)
        return await self._analyses.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=limit
        )


class CreateDAGUseCase:
    def __init__(
        self,
        dags: DAGVersionRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._dags = dags
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization
        self._manager = DAGManager()

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        name: str,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        variable_roles: dict[str, str],
        version_id: UUID | None = None,
        description: str | None = None,
    ) -> DAGVersion:
        self._authorization.require_permission(tenant.role, Permission.CAUSAL_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return await self._manager.save_dag(
            repo=self._dags,
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            created_by=tenant.user_id,
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            variable_roles=variable_roles,
        )


class UpdateDAGUseCase(CreateDAGUseCase):
    async def execute_update(  # type: ignore[override]
        self,
        *,
        tenant: TenantContext,
        dag_id: UUID,
        dataset_id: UUID,
        name: str,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        variable_roles: dict[str, str],
        version_id: UUID | None = None,
        description: str | None = None,
    ) -> DAGVersion:
        self._authorization.require_permission(tenant.role, Permission.CAUSAL_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return await self._manager.save_dag(
            repo=self._dags,
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            created_by=tenant.user_id,
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            variable_roles=variable_roles,
            dag_id=dag_id,
        )


class GetDAGUseCase:
    def __init__(
        self,
        dags: DAGVersionRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._dags = dags
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, dag_id: UUID) -> DAGVersion:
        self._authorization.require_permission(tenant.role, Permission.CAUSAL_READ)
        dag = await self._dags.get_by_id(dag_id=dag_id, organization_id=tenant.organization_id)
        if dag is None:
            raise NotFoundError("DAG not found.")
        return dag


class RefuteCausalAnalysisUseCase:
    def __init__(
        self,
        analyses: CausalAnalysisRepository,
        frame_loader: DatasetFrameLoader,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        from app.application.dto.causal import TreatmentEffectDTO
        from app.application.services.causal.refutation import RefutationEngine

        self._analyses = analyses
        self._frame_loader = frame_loader
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization
        self._refutation = RefutationEngine()

    async def execute(self, *, tenant: TenantContext, analysis_id: UUID) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.CAUSAL_READ)
        run = await self._analyses.get_by_id(
            analysis_id=analysis_id, organization_id=tenant.organization_id
        )
        if run is None:
            raise NotFoundError("Analysis not found.")
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=run.dataset_id, version_id=run.version_id
        )
        sampled = await self._frame_loader.load(version=version)
        te_data = run.result.get("treatment_effect", {})
        original = TreatmentEffectDTO(
            estimator=run.estimator or CausalEstimatorType.DIFFERENCE_IN_MEANS,
            ate=te_data.get("ate"),
            att=te_data.get("att"),
            atc=te_data.get("atc"),
            std_error=te_data.get("std_error"),
            confidence_level=te_data.get("confidence_level", 0.95),
            ci_lower=te_data.get("ci_lower"),
            ci_upper=te_data.get("ci_upper"),
            p_value=te_data.get("p_value"),
            details=te_data.get("details", {}),
        )
        adj = tuple(run.result.get("identification", {}).get("adjustment_set", []))
        results = self._refutation.refute(
            frame=sampled.frame,
            treatment=run.treatment,
            outcome=run.outcome,
            original=original,
            adjustment_set=adj,
        )
        return to_jsonable(results)
