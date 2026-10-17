"""Statistical analysis endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    GetStatisticalAnalysisDep,
    GetStatisticalRecommendationsDep,
    ListStatisticalAnalysisHistoryDep,
    RunStatisticalAnalysisDep,
    TenantContextDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.statistics import (
    AnalysisHistoryItem,
    AnalysisRunResponse,
    AnalyzeRequest,
    RecommendationsRequest,
)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.post(
    "/analyze",
    response_model=DataResponse[AnalysisRunResponse],
    status_code=HTTPStatus.CREATED,
    summary="Run a statistical analysis on a dataset version",
)
async def analyze(
    tenant: TenantContextDep,
    use_case: RunStatisticalAnalysisDep,
    body: AnalyzeRequest,
) -> DataResponse[AnalysisRunResponse]:
    run = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        goal=body.goal,
        research_question=body.research_question,
        variables=[v.model_dump() for v in body.variables],
        version_id=UUID(body.version_id) if body.version_id else None,
        test_type=body.test_type,
        confidence_level=body.confidence_level,
        reference_value=body.reference_value,
    )
    return DataResponse(data=AnalysisRunResponse.from_entity(run))


@router.get(
    "/history",
    response_model=DataResponse[list[AnalysisHistoryItem]],
    summary="List statistical analysis history for a dataset",
)
async def list_history(
    tenant: TenantContextDep,
    use_case: ListStatisticalAnalysisHistoryDep,
    dataset_id: UUID = Query(...),
    version_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[AnalysisHistoryItem]]:
    runs = await use_case.execute(
        tenant=tenant,
        dataset_id=dataset_id,
        version_id=version_id,
        limit=limit,
    )
    return DataResponse(data=[AnalysisHistoryItem.from_entity(r) for r in runs])


@router.post(
    "/recommendations",
    response_model=DataResponse[dict],
    summary="Get statistical test recommendations for a research goal",
)
async def recommendations(
    tenant: TenantContextDep,
    use_case: GetStatisticalRecommendationsDep,
    body: RecommendationsRequest,
) -> DataResponse[dict]:
    result = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        goal=body.goal,
        variables=[v.model_dump() for v in body.variables],
        version_id=UUID(body.version_id) if body.version_id else None,
    )
    return DataResponse(data=result)


@router.get(
    "/{analysis_id}",
    response_model=DataResponse[AnalysisRunResponse],
    summary="Get a statistical analysis result by ID",
)
async def get_analysis(
    tenant: TenantContextDep,
    use_case: GetStatisticalAnalysisDep,
    analysis_id: UUID,
) -> DataResponse[AnalysisRunResponse]:
    run = await use_case.execute(tenant=tenant, analysis_id=analysis_id)
    return DataResponse(data=AnalysisRunResponse.from_entity(run))
