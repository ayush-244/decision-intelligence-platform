"""Project endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import CreateProjectDep, ListProjectsDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.identity import CreateProjectRequest, ProjectResponse
router = APIRouter(prefix="/projects", tags=["projects"])


@router.get(
    "",
    response_model=DataResponse[list[ProjectResponse]],
    summary="List projects in a workspace",
)
async def list_projects(
    tenant: TenantContextDep,
    use_case: ListProjectsDep,
    workspace_id: UUID = Query(..., description="Workspace to list projects from"),
) -> DataResponse[list[ProjectResponse]]:
    rows = await use_case.execute(tenant=tenant, workspace_id=workspace_id)
    return DataResponse(data=[ProjectResponse.from_dto(row) for row in rows])


@router.post(
    "",
    response_model=DataResponse[ProjectResponse],
    status_code=HTTPStatus.CREATED,
    summary="Create a project in a workspace",
)
async def create_project(
    body: CreateProjectRequest,
    tenant: TenantContextDep,
    use_case: CreateProjectDep,
) -> DataResponse[ProjectResponse]:
    project = await use_case.execute(
        tenant=tenant,
        workspace_id=body.workspace_id,
        name=body.name,
        description=body.description,
    )
    return DataResponse(data=ProjectResponse.from_dto(project))
