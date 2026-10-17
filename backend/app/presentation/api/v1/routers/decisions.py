"""Decision intelligence endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    GetDecisionDep,
    ListDecisionHistoryDep,
    RunDecisionAnalysisDep,
    TenantContextDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.decision import (
    DecisionAnalyzeRequest,
    DecisionHistoryItem,
    DecisionResponse,
)

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post(
    "/analyze",
    response_model=DataResponse[DecisionResponse],
    status_code=HTTPStatus.CREATED,
    summary="Run decision intelligence analysis on simulations",
)
async def analyze(
    tenant: TenantContextDep,
    use_case: RunDecisionAnalysisDep,
    body: DecisionAnalyzeRequest,
) -> DataResponse[DecisionResponse]:
    run = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        name=body.name,
        primary_objective=body.primary_objective,
        simulation_run_ids=(
            [UUID(s) for s in body.simulation_run_ids] if body.simulation_run_ids else None
        ),
        version_id=UUID(body.version_id) if body.version_id else None,
        objective_weights=(
            [w.model_dump() for w in body.objective_weights] if body.objective_weights else None
        ),
        constraints=[c.model_dump() for c in body.constraints] if body.constraints else None,
        risk_tolerance=body.risk_tolerance,
        min_confidence=body.min_confidence,
        max_budget=body.max_budget,
    )
    return DataResponse(data=DecisionResponse.from_entity(run))


@router.get(
    "",
    response_model=DataResponse[list[DecisionHistoryItem]],
    summary="List decision analysis history for a dataset",
)
async def list_decisions(
    tenant: TenantContextDep,
    use_case: ListDecisionHistoryDep,
    dataset_id: UUID = Query(...),
    version_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[DecisionHistoryItem]]:
    runs = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id, limit=limit
    )
    return DataResponse(data=[DecisionHistoryItem.from_entity(r) for r in runs])


@router.get(
    "/{decision_id}",
    response_model=DataResponse[DecisionResponse],
    summary="Get a decision analysis by ID",
)
async def get_decision(
    tenant: TenantContextDep,
    use_case: GetDecisionDep,
    decision_id: UUID,
) -> DataResponse[DecisionResponse]:
    run = await use_case.execute(tenant=tenant, decision_id=decision_id)
    return DataResponse(data=DecisionResponse.from_entity(run))
