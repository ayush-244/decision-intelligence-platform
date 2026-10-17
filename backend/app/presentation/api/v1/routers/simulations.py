"""Simulation endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    CalculateROIDep,
    CalculateRiskDep,
    CreateScenarioDep,
    GetScenarioDep,
    GetSimulationDep,
    ListScenariosDep,
    ListSimulationHistoryDep,
    RunSimulationDep,
    TenantContextDep,
    UpdateScenarioDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.simulation import (
    CreateScenarioRequest,
    ROIRequest,
    RiskRequest,
    RunSimulationRequest,
    ScenarioResponse,
    SimulationHistoryItem,
    SimulationResponse,
    UpdateScenarioRequest,
)

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post(
    "",
    response_model=DataResponse[SimulationResponse],
    status_code=HTTPStatus.CREATED,
    summary="Run a counterfactual simulation",
)
async def run_simulation(
    tenant: TenantContextDep,
    use_case: RunSimulationDep,
    body: RunSimulationRequest,
) -> DataResponse[SimulationResponse]:
    run = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        causal_analysis_id=UUID(body.causal_analysis_id),
        name=body.name,
        objective=body.objective,
        scenario_id=UUID(body.scenario_id) if body.scenario_id else None,
        version_id=UUID(body.version_id) if body.version_id else None,
        statistical_analysis_id=(
            UUID(body.statistical_analysis_id) if body.statistical_analysis_id else None
        ),
        interventions=[i.model_dump() for i in body.interventions] if body.interventions else None,
        constraints=[c.model_dump() for c in body.constraints] if body.constraints else None,
        monte_carlo_iterations=body.monte_carlo_iterations,
        confidence_level=body.confidence_level,
        roi_assumptions=body.roi_assumptions,
    )
    return DataResponse(data=SimulationResponse.from_entity(run))


@router.get(
    "/history",
    response_model=DataResponse[list[SimulationHistoryItem]],
    summary="List simulation history for a dataset",
)
async def list_history(
    tenant: TenantContextDep,
    use_case: ListSimulationHistoryDep,
    dataset_id: UUID = Query(...),
    version_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[SimulationHistoryItem]]:
    runs = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id, limit=limit
    )
    return DataResponse(data=[SimulationHistoryItem.from_entity(r) for r in runs])


@router.get(
    "/{simulation_id}",
    response_model=DataResponse[SimulationResponse],
    summary="Get a simulation result by ID",
)
async def get_simulation(
    tenant: TenantContextDep,
    use_case: GetSimulationDep,
    simulation_id: UUID,
) -> DataResponse[SimulationResponse]:
    run = await use_case.execute(tenant=tenant, simulation_id=simulation_id)
    return DataResponse(data=SimulationResponse.from_entity(run))
