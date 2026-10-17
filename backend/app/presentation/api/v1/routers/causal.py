"""Causal inference endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    CreateDAGDep,
    GetCausalAnalysisDep,
    GetDAGDep,
    ListCausalAnalysisHistoryDep,
    RefuteCausalAnalysisDep,
    RunCausalAnalysisDep,
    TenantContextDep,
    UpdateDAGDep,
)
from app.presentation.api.schemas.causal import (
    CausalAnalysisResponse,
    CausalAnalyzeRequest,
    CausalHistoryItem,
    CreateDAGRequest,
    DAGResponse,
    UpdateDAGRequest,
)
from app.presentation.api.schemas.common import DataResponse

router = APIRouter(prefix="/causal", tags=["causal"])


@router.post(
    "/analyze",
    response_model=DataResponse[CausalAnalysisResponse],
    status_code=HTTPStatus.CREATED,
    summary="Run a causal analysis on a dataset version",
)
async def analyze(
    tenant: TenantContextDep,
    use_case: RunCausalAnalysisDep,
    body: CausalAnalyzeRequest,
) -> DataResponse[CausalAnalysisResponse]:
    run = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        treatment=body.treatment,
        outcome=body.outcome,
        business_question=body.business_question,
        version_id=UUID(body.version_id) if body.version_id else None,
        dag_id=UUID(body.dag_id) if body.dag_id else None,
        estimator=body.estimator,
        confidence_level=body.confidence_level,
        adjustment_set=body.adjustment_set,
        run_refutation=body.run_refutation,
        run_sensitivity=body.run_sensitivity,
    )
    return DataResponse(data=CausalAnalysisResponse.from_entity(run))


@router.get(
    "/history",
    response_model=DataResponse[list[CausalHistoryItem]],
    summary="List causal analysis history for a dataset",
)
async def list_history(
    tenant: TenantContextDep,
    use_case: ListCausalAnalysisHistoryDep,
    dataset_id: UUID = Query(...),
    version_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[CausalHistoryItem]]:
    runs = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id, limit=limit
    )
    return DataResponse(data=[CausalHistoryItem.from_entity(r) for r in runs])


@router.post(
    "/dag",
    response_model=DataResponse[DAGResponse],
    status_code=HTTPStatus.CREATED,
    summary="Create a causal DAG",
)
async def create_dag(
    tenant: TenantContextDep,
    use_case: CreateDAGDep,
    body: CreateDAGRequest,
) -> DataResponse[DAGResponse]:
    dag = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        name=body.name,
        nodes=[n.model_dump() for n in body.nodes],
        edges=[e.model_dump() for e in body.edges],
        variable_roles=body.variable_roles,
        version_id=UUID(body.version_id) if body.version_id else None,
        description=body.description,
    )
    return DataResponse(data=DAGResponse.from_entity(dag))


@router.put(
    "/dag/{dag_id}",
    response_model=DataResponse[DAGResponse],
    summary="Update a causal DAG",
)
async def update_dag(
    tenant: TenantContextDep,
    use_case: UpdateDAGDep,
    dag_id: UUID,
    body: UpdateDAGRequest,
) -> DataResponse[DAGResponse]:
    dag = await use_case.execute_update(
        tenant=tenant,
        dag_id=dag_id,
        dataset_id=UUID(body.dataset_id),
        name=body.name,
        nodes=[n.model_dump() for n in body.nodes],
        edges=[e.model_dump() for e in body.edges],
        variable_roles=body.variable_roles,
        version_id=UUID(body.version_id) if body.version_id else None,
        description=body.description,
    )
    return DataResponse(data=DAGResponse.from_entity(dag))


@router.get(
    "/dag/{dag_id}",
    response_model=DataResponse[DAGResponse],
    summary="Get a causal DAG by ID",
)
async def get_dag(
    tenant: TenantContextDep,
    use_case: GetDAGDep,
    dag_id: UUID,
) -> DataResponse[DAGResponse]:
    dag = await use_case.execute(tenant=tenant, dag_id=dag_id)
    return DataResponse(data=DAGResponse.from_entity(dag))


@router.post(
    "/refute",
    response_model=DataResponse[list],
    summary="Re-run refutation tests for an analysis",
)
async def refute(
    tenant: TenantContextDep,
    use_case: RefuteCausalAnalysisDep,
    analysis_id: UUID = Query(...),
) -> DataResponse[list]:
    results = await use_case.execute(tenant=tenant, analysis_id=analysis_id)
    return DataResponse(data=results)


@router.get(
    "/sensitivity",
    response_model=DataResponse[dict],
    summary="Get sensitivity analysis from a completed run",
)
async def sensitivity(
    tenant: TenantContextDep,
    use_case: GetCausalAnalysisDep,
    analysis_id: UUID = Query(...),
) -> DataResponse[dict]:
    run = await use_case.execute(tenant=tenant, analysis_id=analysis_id)
    return DataResponse(data=run.result.get("sensitivity") or {})


@router.get(
    "/{analysis_id}",
    response_model=DataResponse[CausalAnalysisResponse],
    summary="Get a causal analysis result by ID",
)
async def get_analysis(
    tenant: TenantContextDep,
    use_case: GetCausalAnalysisDep,
    analysis_id: UUID,
) -> DataResponse[CausalAnalysisResponse]:
    run = await use_case.execute(tenant=tenant, analysis_id=analysis_id)
    return DataResponse(data=CausalAnalysisResponse.from_entity(run))
