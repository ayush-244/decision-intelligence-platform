"""Background job endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.application.dto.infrastructure import SubmitJobRequestDTO
from app.presentation.api.deps import (
    CancelAnalyticsJobDep,
    GetAnalyticsJobDep,
    ListAnalyticsJobsDep,
    RetryAnalyticsJobDep,
    SubmitAnalyticsJobDep,
    TenantContextDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.infrastructure import JobSnapshotResponse, SubmitJobRequest

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=DataResponse[JobSnapshotResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a background analytics job",
)
async def submit_job(
    tenant: TenantContextDep,
    use_case: SubmitAnalyticsJobDep,
    body: SubmitJobRequest,
) -> DataResponse[JobSnapshotResponse]:
    snapshot = await use_case.execute(
        tenant=tenant,
        request=SubmitJobRequestDTO(
            job_type=body.job_type,
            name=body.name,
            dataset_id=body.dataset_id,
            version_id=body.version_id,
            resource_type=body.resource_type,
            resource_id=body.resource_id,
            configuration=body.configuration,
        ),
    )
    return DataResponse(data=JobSnapshotResponse.from_dto(snapshot))


@router.get(
    "",
    response_model=DataResponse[list[JobSnapshotResponse]],
    summary="List analytics jobs for the organization",
)
async def list_jobs(
    tenant: TenantContextDep,
    use_case: ListAnalyticsJobsDep,
    status_filter: str | None = Query(None, alias="status"),
    job_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> DataResponse[list[JobSnapshotResponse]]:
    snapshots = await use_case.execute(
        tenant=tenant, status=status_filter, job_type=job_type, limit=limit
    )
    return DataResponse(data=[JobSnapshotResponse.from_dto(s) for s in snapshots])


@router.get(
    "/{job_id}",
    response_model=DataResponse[JobSnapshotResponse],
    summary="Get job status and execution details",
)
async def get_job(
    tenant: TenantContextDep,
    use_case: GetAnalyticsJobDep,
    job_id: UUID,
) -> DataResponse[JobSnapshotResponse]:
    snapshot = await use_case.execute(tenant=tenant, job_id=job_id)
    return DataResponse(data=JobSnapshotResponse.from_dto(snapshot))


@router.post(
    "/{job_id}/cancel",
    response_model=DataResponse[JobSnapshotResponse],
    summary="Cancel a queued or running job",
)
async def cancel_job(
    tenant: TenantContextDep,
    use_case: CancelAnalyticsJobDep,
    job_id: UUID,
) -> DataResponse[JobSnapshotResponse]:
    snapshot = await use_case.execute(tenant=tenant, job_id=job_id)
    return DataResponse(data=JobSnapshotResponse.from_dto(snapshot))


@router.post(
    "/{job_id}/retry",
    response_model=DataResponse[JobSnapshotResponse],
    summary="Retry a failed job",
)
async def retry_job(
    tenant: TenantContextDep,
    use_case: RetryAnalyticsJobDep,
    job_id: UUID,
) -> DataResponse[JobSnapshotResponse]:
    snapshot = await use_case.execute(tenant=tenant, job_id=job_id)
    return DataResponse(data=JobSnapshotResponse.from_dto(snapshot))
