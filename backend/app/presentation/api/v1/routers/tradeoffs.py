"""Tradeoff analysis endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import GetTradeoffsDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse

router = APIRouter(prefix="/tradeoffs", tags=["tradeoffs"])


@router.get("", response_model=DataResponse[list], summary="Get tradeoff analysis")
async def list_tradeoffs(
    tenant: TenantContextDep,
    use_case: GetTradeoffsDep,
    decision_id: UUID = Query(...),
) -> DataResponse[list]:
    items = await use_case.execute_tradeoffs(tenant=tenant, decision_id=decision_id)
    return DataResponse(data=items)
