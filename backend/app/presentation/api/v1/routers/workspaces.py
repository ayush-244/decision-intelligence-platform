"""Workspace endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import CreateWorkspaceDep, ListWorkspacesDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.identity import CreateWorkspaceRequest, WorkspaceResponse
from app.shared.exceptions import BusinessValidationError

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get(
    "",
    response_model=DataResponse[list[WorkspaceResponse]],
    summary="List workspaces in the active organization",
)
async def list_workspaces(
    tenant: TenantContextDep,
    use_case: ListWorkspacesDep,
    organization_id: UUID | None = Query(default=None, description="Deprecated — use X-Organization-ID"),
) -> DataResponse[list[WorkspaceResponse]]:
    if organization_id is not None and organization_id != tenant.organization_id:
        raise BusinessValidationError("organization_id query must match X-Organization-ID header.")
    rows = await use_case.execute(tenant=tenant)
    return DataResponse(data=[WorkspaceResponse.from_dto(row) for row in rows])


@router.post(
    "",
    response_model=DataResponse[WorkspaceResponse],
    status_code=HTTPStatus.CREATED,
    summary="Create a workspace in the active organization",
)
async def create_workspace(
    body: CreateWorkspaceRequest,
    tenant: TenantContextDep,
    use_case: CreateWorkspaceDep,
) -> DataResponse[WorkspaceResponse]:
    if body.organization_id != tenant.organization_id:
        raise BusinessValidationError("organization_id must match X-Organization-ID header.")
    workspace = await use_case.execute(
        tenant=tenant,
        name=body.name,
        description=body.description,
    )
    return DataResponse(data=WorkspaceResponse.from_dto(workspace))
