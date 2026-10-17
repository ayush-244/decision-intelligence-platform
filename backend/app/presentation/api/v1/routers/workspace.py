"""Unified workspace endpoints — search, comparison, activity."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    CompareSessionsDep,
    ListWorkspaceActivityDep,
    TenantContextDep,
    WorkspaceSearchDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.workspace import CompareSessionsRequest

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get(
    "/search",
    response_model=DataResponse[list[dict]],
    summary="Global workspace search",
)
async def workspace_search(
    tenant: TenantContextDep,
    use_case: WorkspaceSearchDep,
    q: str = Query(..., min_length=1),
    dataset_id: UUID | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
) -> DataResponse[list[dict]]:
    results = await use_case.execute(
        tenant=tenant, query=q, dataset_id=dataset_id, limit=limit
    )
    return DataResponse(data=results)


@router.post(
    "/compare",
    response_model=DataResponse[dict],
    summary="Compare two decision sessions",
)
async def compare_sessions(
    tenant: TenantContextDep,
    use_case: CompareSessionsDep,
    body: CompareSessionsRequest,
) -> DataResponse[dict]:
    result = await use_case.execute(
        tenant=tenant,
        session_a_id=UUID(body.session_a_id),
        session_b_id=UUID(body.session_b_id),
    )
    return DataResponse(data=result)


@router.get(
    "/activity",
    response_model=DataResponse[list[dict]],
    summary="Organization activity and audit history",
)
async def workspace_activity(
    tenant: TenantContextDep,
    use_case: ListWorkspaceActivityDep,
    limit: int = Query(default=50, ge=1, le=200),
    resource_type: str | None = Query(default=None),
) -> DataResponse[list[dict]]:
    logs = await use_case.execute(
        tenant=tenant, limit=limit, resource_type=resource_type
    )
    return DataResponse(data=logs)
