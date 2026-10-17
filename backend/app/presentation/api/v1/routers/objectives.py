"""Business objective catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.deps import ListObjectivesDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse

router = APIRouter(prefix="/objectives", tags=["objectives"])


@router.get("", response_model=DataResponse[list], summary="List supported decision objectives")
async def list_objectives(
    tenant: TenantContextDep,
    use_case: ListObjectivesDep,
) -> DataResponse[list]:
    items = await use_case.execute(tenant=tenant)
    return DataResponse(data=items)
