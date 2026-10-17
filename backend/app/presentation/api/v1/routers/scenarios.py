"""Scenario management endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    CreateScenarioDep,
    GetScenarioDep,
    ListScenariosDep,
    TenantContextDep,
    UpdateScenarioDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.simulation import (
    CreateScenarioRequest,
    ScenarioResponse,
    UpdateScenarioRequest,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post(
    "",
    response_model=DataResponse[ScenarioResponse],
    status_code=HTTPStatus.CREATED,
    summary="Create a business scenario",
)
async def create_scenario(
    tenant: TenantContextDep,
    use_case: CreateScenarioDep,
    body: CreateScenarioRequest,
) -> DataResponse[ScenarioResponse]:
    scenario = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        name=body.name,
        interventions=[i.model_dump() for i in body.interventions],
        constraints=[c.model_dump() for c in body.constraints],
        version_id=UUID(body.version_id) if body.version_id else None,
        description=body.description,
        objective=body.objective,
        notes=body.notes,
        is_baseline=body.is_baseline,
    )
    return DataResponse(data=ScenarioResponse.from_entity(scenario))


@router.put(
    "/{scenario_id}",
    response_model=DataResponse[ScenarioResponse],
    summary="Update a business scenario",
)
async def update_scenario(
    tenant: TenantContextDep,
    use_case: UpdateScenarioDep,
    scenario_id: UUID,
    body: UpdateScenarioRequest,
) -> DataResponse[ScenarioResponse]:
    scenario = await use_case.execute_update(
        tenant=tenant,
        scenario_id=scenario_id,
        dataset_id=UUID(body.dataset_id),
        name=body.name,
        interventions=[i.model_dump() for i in body.interventions],
        constraints=[c.model_dump() for c in body.constraints],
        version_id=UUID(body.version_id) if body.version_id else None,
        description=body.description,
        objective=body.objective,
        notes=body.notes,
    )
    return DataResponse(data=ScenarioResponse.from_entity(scenario))


@router.get(
    "",
    response_model=DataResponse[list[ScenarioResponse]],
    summary="List scenarios for a dataset",
)
async def list_scenarios(
    tenant: TenantContextDep,
    use_case: ListScenariosDep,
    dataset_id: UUID = Query(...),
    version_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[ScenarioResponse]]:
    scenarios = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id, limit=limit
    )
    return DataResponse(data=[ScenarioResponse.from_entity(s) for s in scenarios])


@router.get(
    "/{scenario_id}",
    response_model=DataResponse[ScenarioResponse],
    summary="Get a scenario by ID",
)
async def get_scenario(
    tenant: TenantContextDep,
    use_case: GetScenarioDep,
    scenario_id: UUID,
) -> DataResponse[ScenarioResponse]:
    scenario = await use_case.execute(tenant=tenant, scenario_id=scenario_id)
    return DataResponse(data=ScenarioResponse.from_entity(scenario))
