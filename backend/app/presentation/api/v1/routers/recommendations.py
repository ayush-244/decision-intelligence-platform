"""Recommendation endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import GetRecommendationsDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get(
    "",
    response_model=DataResponse[list],
    summary="Get ranked recommendations from a decision analysis",
)
async def list_recommendations(
    tenant: TenantContextDep,
    use_case: GetRecommendationsDep,
    decision_id: UUID = Query(...),
) -> DataResponse[list]:
    items = await use_case.execute_recommendations(tenant=tenant, decision_id=decision_id)
    return DataResponse(data=items)
