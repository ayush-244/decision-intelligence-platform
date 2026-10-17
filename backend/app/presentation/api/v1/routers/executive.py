"""Executive dashboard endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import GetExecutiveDashboardDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse

router = APIRouter(prefix="/executive", tags=["executive"])


@router.get(
    "/dashboard",
    response_model=DataResponse[dict],
    summary="Executive dashboard snapshot for a dataset",
)
async def executive_dashboard(
    tenant: TenantContextDep,
    use_case: GetExecutiveDashboardDep,
    dataset_id: UUID = Query(...),
) -> DataResponse[dict]:
    data = await use_case.execute(tenant=tenant, dataset_id=dataset_id)
    return DataResponse(data=data)
