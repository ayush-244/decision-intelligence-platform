"""Priority ranking endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import GetPrioritiesDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse

router = APIRouter(prefix="/priorities", tags=["priorities"])


@router.get("", response_model=DataResponse[list], summary="Get implementation priorities")
async def list_priorities(
    tenant: TenantContextDep,
    use_case: GetPrioritiesDep,
    decision_id: UUID = Query(...),
) -> DataResponse[list]:
    items = await use_case.execute_priorities(tenant=tenant, decision_id=decision_id)
    return DataResponse(data=items)
