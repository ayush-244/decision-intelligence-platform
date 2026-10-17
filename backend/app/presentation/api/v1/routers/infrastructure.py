"""Infrastructure monitoring endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.presentation.api.deps import (
    GetCacheStatsDep,
    GetInfrastructureMetricsDep,
    GetQueueStatusDep,
    InvalidateDatasetCacheDep,
    TenantContextDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.infrastructure import (
    InfrastructureMetricsResponse,
    InvalidateCacheRequest,
)

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


@router.get(
    "/metrics",
    response_model=DataResponse[InfrastructureMetricsResponse],
    summary="Infrastructure and job metrics snapshot",
)
async def infrastructure_metrics(
    tenant: TenantContextDep,
    use_case: GetInfrastructureMetricsDep,
) -> DataResponse[InfrastructureMetricsResponse]:
    metrics = await use_case.execute(tenant=tenant)
    return DataResponse(
        data=InfrastructureMetricsResponse(
            queue_depth=metrics.queue_depth,
            jobs_queued=metrics.jobs_queued,
            jobs_running=metrics.jobs_running,
            jobs_completed_24h=metrics.jobs_completed_24h,
            jobs_failed_24h=metrics.jobs_failed_24h,
            cache_hits=metrics.cache_hits,
            cache_misses=metrics.cache_misses,
            cache_keys=metrics.cache_keys,
            avg_job_duration_ms=metrics.avg_job_duration_ms,
            slow_queries_detected=metrics.slow_queries_detected,
        )
    )


@router.get(
    "/cache/stats",
    response_model=DataResponse[dict],
    summary="Analytics cache statistics",
)
async def cache_stats(
    tenant: TenantContextDep,
    use_case: GetCacheStatsDep,
) -> DataResponse[dict]:
    stats = await use_case.execute(tenant=tenant)
    return DataResponse(data=stats)


@router.post(
    "/cache/invalidate",
    response_model=DataResponse[dict],
    summary="Invalidate version-aware cache for a dataset",
)
async def invalidate_cache(
    tenant: TenantContextDep,
    use_case: InvalidateDatasetCacheDep,
    body: InvalidateCacheRequest,
) -> DataResponse[dict]:
    result = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        version_id=UUID(body.version_id) if body.version_id else None,
    )
    return DataResponse(data=result)


@router.get(
    "/queue",
    response_model=DataResponse[dict],
    summary="Execution queue depth",
)
async def queue_status(
    tenant: TenantContextDep,
    use_case: GetQueueStatusDep,
) -> DataResponse[dict]:
    status_payload = await use_case.execute(tenant=tenant)
    return DataResponse(data=status_payload)
