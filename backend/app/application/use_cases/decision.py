"""Decision intelligence use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.decision import (
    DecisionConstraintDTO,
    DecisionRequestDTO,
    ObjectiveWeightDTO,
)
from app.application.services.decision.engine import DecisionEngine
from app.domain.entities.decision_run import DecisionRun
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
from app.domain.value_objects.decision import DecisionObjective, DecisionRunStatus
from app.domain.value_objects.role import Permission
from app.domain.value_objects.simulation import SimulationRunStatus
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


class RunDecisionAnalysisUseCase:
    def __init__(
        self,
        engine: DecisionEngine,
        simulations: SimulationRunRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._simulations = simulations
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        name: str,
        primary_objective: str,
        simulation_run_ids: list[UUID] | None = None,
        version_id: UUID | None = None,
        objective_weights: list[dict[str, Any]] | None = None,
        constraints: list[dict[str, Any]] | None = None,
        risk_tolerance: float = 0.65,
        min_confidence: float = 0.5,
        max_budget: float | None = None,
    ) -> DecisionRun:
        self._authorization.require_permission(tenant.role, Permission.DECISION_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )

        if simulation_run_ids:
            sim_runs = []
            for sid in simulation_run_ids:
                run = await self._simulations.get_by_id(
                    simulation_id=sid, organization_id=tenant.organization_id
                )
                if run is None or run.dataset_id != dataset_id:
                    raise NotFoundError(f"Simulation {sid} not found.")
                if run.status is not SimulationRunStatus.COMPLETED:
                    raise BusinessValidationError(
                        f"Simulation {sid} is not completed.", code="simulation_incomplete"
                    )
                sim_runs.append(run)
        else:
            sim_runs = await self._simulations.list_for_dataset(
                dataset_id=dataset_id,
                organization_id=tenant.organization_id,
                limit=50,
            )
            sim_runs = [r for r in sim_runs if r.status is SimulationRunStatus.COMPLETED]

        weight_dtos = tuple(
            ObjectiveWeightDTO(objective=w["objective"], weight=float(w["weight"]))
            for w in (objective_weights or [])
        )
        constraint_dtos = tuple(
            DecisionConstraintDTO(
                type=c.get("type", "custom"),
                severity=c.get("severity", "soft"),
                threshold=c.get("threshold"),
                description=c.get("description", ""),
            )
            for c in (constraints or [])
        )

        request = DecisionRequestDTO(
            dataset_id=str(dataset_id),
            version_id=str(version.id),
            name=name,
            primary_objective=primary_objective,
            simulation_run_ids=tuple(str(s) for s in (simulation_run_ids or [r.id for r in sim_runs])),
            objective_weights=weight_dtos,
            constraints=constraint_dtos,
            risk_tolerance=risk_tolerance,
            min_confidence=min_confidence,
            max_budget=max_budget,
        )
        return await self._engine.analyze(
            dataset=dataset,
            version=version,
            request=request,
            simulation_runs=sim_runs,
            created_by=tenant.user_id,
        )


class GetDecisionUseCase:
    def __init__(
        self,
        decisions: DecisionRunRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._decisions = decisions
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, decision_id: UUID) -> DecisionRun:
        self._authorization.require_permission(tenant.role, Permission.DECISION_READ)
        run = await self._decisions.get_by_id(
            decision_id=decision_id, organization_id=tenant.organization_id
        )
        if run is None:
            raise NotFoundError("Decision analysis not found.")
        if run.status is DecisionRunStatus.FAILED:
            raise BusinessValidationError(
                run.error_message or "Decision analysis failed.", code="decision_failed"
            )
        return run


class ListDecisionHistoryUseCase:
    def __init__(
        self,
        decisions: DecisionRunRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._decisions = decisions
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
        limit: int = 50,
    ) -> list[DecisionRun]:
        self._authorization.require_permission(tenant.role, Permission.DECISION_READ)
        if version_id:
            await self._guard.resolve_version(
                tenant=tenant, dataset_id=dataset_id, version_id=version_id
            )
            return await self._decisions.list_for_version(
                version_id=version_id, organization_id=tenant.organization_id, limit=limit
            )
        await self._guard.resolve_version(tenant=tenant, dataset_id=dataset_id, version_id=None)
        return await self._decisions.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=limit
        )


class ListObjectivesUseCase:
    def __init__(self, authorization: AuthorizationService) -> None:
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext) -> list[dict[str, str]]:
        self._authorization.require_permission(tenant.role, Permission.DECISION_READ)
        return [
            {"id": obj.value, "label": obj.value.replace("_", " ").title()}
            for obj in DecisionObjective
        ]


class GetRecommendationsUseCase(GetDecisionUseCase):
    async def execute_recommendations(  # type: ignore[override]
        self, *, tenant: TenantContext, decision_id: UUID
    ) -> list[dict[str, Any]]:
        run = await self.execute(tenant=tenant, decision_id=decision_id)
        return list(run.result.get("recommendations", []))


class GetTradeoffsUseCase(GetDecisionUseCase):
    async def execute_tradeoffs(self, *, tenant: TenantContext, decision_id: UUID) -> list[dict[str, Any]]:
        run = await self.execute(tenant=tenant, decision_id=decision_id)
        return list(run.result.get("tradeoffs", []))


class GetPrioritiesUseCase(GetDecisionUseCase):
    async def execute_priorities(self, *, tenant: TenantContext, decision_id: UUID) -> list[dict[str, Any]]:
        run = await self.execute(tenant=tenant, decision_id=decision_id)
        return list(run.result.get("priorities", []))
