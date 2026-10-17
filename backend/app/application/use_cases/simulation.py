"""Simulation use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.simulation import (
    ConstraintDTO,
    InterventionDTO,
    SimulationRequestDTO,
)
from app.application.services.simulation.engine import SimulationEngine
from app.application.services.simulation.roi import ROICalculator
from app.application.services.simulation.risk import RiskEngine
from app.application.services.simulation.scenario_builder import ScenarioBuilder
from app.application.services.simulation.serialization import to_jsonable
from app.domain.entities.simulation_run import SimulationRun
from app.domain.entities.simulation_scenario import SimulationScenario
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.dataset_version_repository import DatasetVersionRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.simulation_scenario_repository import SimulationScenarioRepository
from app.domain.repositories.workspace_repository import WorkspaceRepository
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
            raise NotFoundError("Dataset has no versions to analyze.")
        version = await self._versions.get_by_id(version_id=target_version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found.")
        return dataset, version


class RunSimulationUseCase:
    def __init__(
        self,
        engine: SimulationEngine,
        scenarios: SimulationScenarioRepository,
        causal_analyses: CausalAnalysisRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._engine = engine
        self._scenarios = scenarios
        self._causal = causal_analyses
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        causal_analysis_id: UUID,
        name: str,
        objective: str,
        scenario_id: UUID | None = None,
        version_id: UUID | None = None,
        statistical_analysis_id: UUID | None = None,
        interventions: list[dict[str, Any]] | None = None,
        constraints: list[dict[str, Any]] | None = None,
        monte_carlo_iterations: int = 1000,
        confidence_level: float = 0.95,
        roi_assumptions: dict[str, Any] | None = None,
    ) -> SimulationRun:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        causal_run = await self._causal.get_by_id(
            analysis_id=causal_analysis_id, organization_id=tenant.organization_id
        )
        if causal_run is None:
            raise NotFoundError("Causal analysis not found.")

        scenario: SimulationScenario
        if scenario_id:
            found = await self._scenarios.get_by_id(
                scenario_id=scenario_id, organization_id=tenant.organization_id
            )
            if found is None:
                raise NotFoundError("Scenario not found.")
            scenario = found
        else:
            builder = ScenarioBuilder()
            scenario = await builder.save_scenario(
                repo=self._scenarios,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                created_by=tenant.user_id,
                name=name,
                objective=objective,
                interventions=interventions or [],
                constraints=constraints or [],
            )

        intervention_dtos = tuple(
            InterventionDTO(
                variable=i["variable"],
                mode=i.get("mode", "relative"),
                value=i["value"],
                reason=i.get("reason"),
            )
            for i in (interventions or scenario.interventions)
        )
        constraint_dtos = tuple(
            ConstraintDTO(
                type=c.get("type", "custom"),
                severity=c.get("severity", "soft"),
                threshold=c.get("threshold"),
                description=c.get("description", ""),
                value=c.get("value"),
            )
            for c in (constraints or scenario.constraints)
        )

        request = SimulationRequestDTO(
            dataset_id=str(dataset_id),
            version_id=str(version.id),
            causal_analysis_id=str(causal_analysis_id),
            statistical_analysis_id=str(statistical_analysis_id) if statistical_analysis_id else None,
            scenario_id=str(scenario.id),
            name=name,
            objective=objective,
            interventions=intervention_dtos,
            constraints=constraint_dtos,
            comparison_scenario_ids=(),
            monte_carlo_iterations=monte_carlo_iterations,
            confidence_level=confidence_level,
            roi_assumptions=roi_assumptions or {},
        )
        return await self._engine.simulate(
            dataset=dataset,
            version=version,
            causal_run=causal_run,
            scenario=scenario,
            request=request,
            created_by=tenant.user_id,
            statistical_analysis_id=statistical_analysis_id,
        )


class GetSimulationUseCase:
    def __init__(
        self,
        runs: SimulationRunRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._runs = runs
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, simulation_id: UUID) -> SimulationRun:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_READ)
        run = await self._runs.get_by_id(
            simulation_id=simulation_id, organization_id=tenant.organization_id
        )
        if run is None:
            raise NotFoundError("Simulation not found.")
        if run.status is SimulationRunStatus.FAILED:
            raise BusinessValidationError(
                run.error_message or "Simulation failed.", code="simulation_failed"
            )
        return run


class ListSimulationHistoryUseCase:
    def __init__(
        self,
        runs: SimulationRunRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._runs = runs
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
        limit: int = 50,
    ) -> list[SimulationRun]:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_READ)
        if version_id:
            await self._guard.resolve_version(
                tenant=tenant, dataset_id=dataset_id, version_id=version_id
            )
            return await self._runs.list_for_version(
                version_id=version_id, organization_id=tenant.organization_id, limit=limit
            )
        await self._guard.resolve_version(tenant=tenant, dataset_id=dataset_id, version_id=None)
        return await self._runs.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=limit
        )


class CreateScenarioUseCase:
    def __init__(
        self,
        scenarios: SimulationScenarioRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._scenarios = scenarios
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization
        self._builder = ScenarioBuilder()

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        name: str,
        interventions: list[dict[str, Any]],
        constraints: list[dict[str, Any]] | None = None,
        version_id: UUID | None = None,
        description: str | None = None,
        objective: str | None = None,
        notes: str | None = None,
        is_baseline: bool = False,
    ) -> SimulationScenario:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return await self._builder.save_scenario(
            repo=self._scenarios,
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            created_by=tenant.user_id,
            name=name,
            interventions=interventions,
            constraints=constraints or [],
            description=description,
            objective=objective,
            notes=notes,
            is_baseline=is_baseline,
        )


class UpdateScenarioUseCase(CreateScenarioUseCase):
    async def execute_update(  # type: ignore[override]
        self,
        *,
        tenant: TenantContext,
        scenario_id: UUID,
        dataset_id: UUID,
        name: str,
        interventions: list[dict[str, Any]],
        constraints: list[dict[str, Any]] | None = None,
        version_id: UUID | None = None,
        description: str | None = None,
        objective: str | None = None,
        notes: str | None = None,
    ) -> SimulationScenario:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_CREATE)
        dataset, version = await self._guard.resolve_version(
            tenant=tenant, dataset_id=dataset_id, version_id=version_id
        )
        return await self._builder.save_scenario(
            repo=self._scenarios,
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            created_by=tenant.user_id,
            name=name,
            interventions=interventions,
            constraints=constraints or [],
            description=description,
            objective=objective,
            notes=notes,
            scenario_id=scenario_id,
        )


class ListScenariosUseCase:
    def __init__(
        self,
        scenarios: SimulationScenarioRepository,
        datasets: DatasetRepository,
        versions: DatasetVersionRepository,
        projects: ProjectRepository,
        workspaces: WorkspaceRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._scenarios = scenarios
        self._guard = _DatasetAccessGuard(datasets, versions, projects, workspaces)
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
        limit: int = 50,
    ) -> list[SimulationScenario]:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_READ)
        await self._guard.resolve_version(tenant=tenant, dataset_id=dataset_id, version_id=version_id)
        return await self._scenarios.list_for_dataset(
            dataset_id=dataset_id, organization_id=tenant.organization_id, limit=limit
        )


class GetScenarioUseCase:
    def __init__(
        self,
        scenarios: SimulationScenarioRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._scenarios = scenarios
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, scenario_id: UUID) -> SimulationScenario:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_READ)
        scenario = await self._scenarios.get_by_id(
            scenario_id=scenario_id, organization_id=tenant.organization_id
        )
        if scenario is None:
            raise NotFoundError("Scenario not found.")
        return scenario


class CalculateROIUseCase:
    def __init__(self, authorization: AuthorizationService) -> None:
        self._authorization = authorization
        self._calculator = ROICalculator()

    async def execute(
        self,
        *,
        tenant: TenantContext,
        counterfactual: dict[str, Any],
        roi_assumptions: dict[str, Any],
    ) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_READ)
        result = self._calculator.calculate_from_payload(
            counterfactual_data=counterfactual,
            roi_assumptions=roi_assumptions,
        )
        return to_jsonable(result)


class CalculateRiskUseCase:
    def __init__(self, authorization: AuthorizationService) -> None:
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        counterfactual: dict[str, Any],
        causal_result: dict[str, Any],
        constraints: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.SIMULATION_READ)
        result = RiskEngine.assess_from_payload(
            counterfactual_data=counterfactual,
            causal_result=causal_result,
            constraints=constraints,
        )
        return to_jsonable(result)
