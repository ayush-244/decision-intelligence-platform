"""Organization endpoints."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import APIRouter

from app.presentation.api.deps import (
    CreateOrganizationDep,
    CurrentUserIdDep,
    ListOrganizationsDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.identity import (
    CreateOrganizationRequest,
    OrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get(
    "",
    response_model=DataResponse[list[OrganizationResponse]],
    summary="List organizations the current user belongs to",
)
async def list_organizations(
    user_id: CurrentUserIdDep,
    use_case: ListOrganizationsDep,
) -> DataResponse[list[OrganizationResponse]]:
    rows = await use_case.execute(user_id=user_id)
    return DataResponse(data=[OrganizationResponse.from_dto(row) for row in rows])


@router.post(
    "",
    response_model=DataResponse[OrganizationResponse],
    status_code=HTTPStatus.CREATED,
    summary="Create a new organization",
)
async def create_organization(
    body: CreateOrganizationRequest,
    user_id: CurrentUserIdDep,
    use_case: CreateOrganizationDep,
) -> DataResponse[OrganizationResponse]:
    org = await use_case.execute(user_id=user_id, name=body.name)
    return DataResponse(data=OrganizationResponse.from_dto(org))
