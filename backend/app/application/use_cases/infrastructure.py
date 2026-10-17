"""Infrastructure use cases."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.authorization.authorization_service import AuthorizationService
from app.application.services.audit.audit_service import AuditService
from app.application.dto.infrastructure import (
    InfrastructureMetricsDTO,
    JobSnapshotDTO,
    SubmitJobRequestDTO,
)
from app.application.services.infrastructure.cache_service import AnalyticsCacheService
from app.application.services.infrastructure.execution_monitor import ExecutionMonitor
from app.application.services.infrastructure.job_orchestrator import JobOrchestrator
from app.application.services.infrastructure.metrics_service import InfrastructureMetricsService
from app.application.services.infrastructure.queue_manager import QueueManager
from app.domain.entities.analytics_job import AnalyticsJob
from app.domain.repositories.analytics_job_repository import AnalyticsJobRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.value_objects.audit_action import AuditAction
from app.domain.value_objects.infrastructure import JobStatus, JobType
from app.domain.value_objects.role import Permission
from app.domain.value_objects.tenant import TenantContext
from app.shared.exceptions import NotFoundError


class SubmitAnalyticsJobUseCase:
    def __init__(
        self,
        orchestrator: JobOrchestrator,
        monitor: ExecutionMonitor,
        datasets: DatasetRepository,
        authorization: AuthorizationService,
        audit: AuditService,
    ) -> None:
        self._orchestrator = orchestrator
        self._monitor = monitor
        self._datasets = datasets
        self._authorization = authorization
        self._audit = audit

    async def execute(
        self,
        *,
        tenant: TenantContext,
        request: SubmitJobRequestDTO,
    ) -> JobSnapshotDTO:
        self._authorization.require_permission(tenant.role, Permission.JOB_CREATE)
        if request.dataset_id:
            dataset = await self._datasets.get_by_id(
                dataset_id=UUID(request.dataset_id),
                organization_id=tenant.organization_id,
            )
            if dataset is None:
                raise NotFoundError("Dataset not found.")
        job = await self._orchestrator.submit(
            organization_id=tenant.organization_id,
            created_by=tenant.user_id,
            request=request,
        )
        await self._audit.record(
            action=AuditAction.JOB_SUBMITTED,
            resource_type="analytics_job",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=job.id,
            metadata={"job_type": job.job_type.value, "name": job.name},
        )
        return self._monitor.snapshot(job)


class ListAnalyticsJobsUseCase:
    def __init__(
        self,
        jobs: AnalyticsJobRepository,
        monitor: ExecutionMonitor,
        authorization: AuthorizationService,
    ) -> None:
        self._jobs = jobs
        self._monitor = monitor
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 50,
    ) -> list[JobSnapshotDTO]:
        self._authorization.require_permission(tenant.role, Permission.JOB_READ)
        parsed_status = JobStatus(status) if status else None
        parsed_type = JobType(job_type) if job_type else None
        rows = await self._jobs.list_for_organization(
            organization_id=tenant.organization_id,
            status=parsed_status,
            job_type=parsed_type,
            limit=limit,
        )
        return [self._monitor.snapshot(job) for job in rows]


class GetAnalyticsJobUseCase:
    def __init__(
        self,
        orchestrator: JobOrchestrator,
        monitor: ExecutionMonitor,
        authorization: AuthorizationService,
    ) -> None:
        self._orchestrator = orchestrator
        self._monitor = monitor
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext, job_id: UUID) -> JobSnapshotDTO:
        self._authorization.require_permission(tenant.role, Permission.JOB_READ)
        job = await self._orchestrator.get(
            job_id=job_id, organization_id=tenant.organization_id
        )
        return self._monitor.snapshot(job)


class CancelAnalyticsJobUseCase:
    def __init__(
        self,
        orchestrator: JobOrchestrator,
        monitor: ExecutionMonitor,
        authorization: AuthorizationService,
        audit: AuditService,
    ) -> None:
        self._orchestrator = orchestrator
        self._monitor = monitor
        self._authorization = authorization
        self._audit = audit

    async def execute(self, *, tenant: TenantContext, job_id: UUID) -> JobSnapshotDTO:
        self._authorization.require_permission(tenant.role, Permission.JOB_CANCEL)
        job = await self._orchestrator.get(
            job_id=job_id, organization_id=tenant.organization_id
        )
        cancelled = await self._orchestrator.cancel(job=job)
        await self._audit.record(
            action=AuditAction.JOB_CANCELLED,
            resource_type="analytics_job",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=job_id,
        )
        return self._monitor.snapshot(cancelled)


class RetryAnalyticsJobUseCase:
    def __init__(
        self,
        orchestrator: JobOrchestrator,
        monitor: ExecutionMonitor,
        authorization: AuthorizationService,
        audit: AuditService,
    ) -> None:
        self._orchestrator = orchestrator
        self._monitor = monitor
        self._authorization = authorization
        self._audit = audit

    async def execute(self, *, tenant: TenantContext, job_id: UUID) -> JobSnapshotDTO:
        self._authorization.require_permission(tenant.role, Permission.JOB_CANCEL)
        job = await self._orchestrator.get(
            job_id=job_id, organization_id=tenant.organization_id
        )
        retried = await self._orchestrator.retry(job=job)
        await self._audit.record(
            action=AuditAction.JOB_RETRIED,
            resource_type="analytics_job",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=job_id,
            metadata={"retry_count": retried.retry_count},
        )
        return self._monitor.snapshot(retried)


class GetInfrastructureMetricsUseCase:
    def __init__(
        self,
        metrics: InfrastructureMetricsService,
        authorization: AuthorizationService,
    ) -> None:
        self._metrics = metrics
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext) -> InfrastructureMetricsDTO:
        self._authorization.require_permission(tenant.role, Permission.INFRA_READ)
        return await self._metrics.snapshot(organization_id=tenant.organization_id)


class GetCacheStatsUseCase:
    def __init__(
        self,
        cache: AnalyticsCacheService,
        authorization: AuthorizationService,
    ) -> None:
        self._cache = cache
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.INFRA_READ)
        stats = await self._cache.stats()
        return {"organization_id": str(tenant.organization_id), **stats}


class InvalidateDatasetCacheUseCase:
    def __init__(
        self,
        cache: AnalyticsCacheService,
        datasets: DatasetRepository,
        authorization: AuthorizationService,
        audit: AuditService,
    ) -> None:
        self._cache = cache
        self._datasets = datasets
        self._authorization = authorization
        self._audit = audit

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        version_id: UUID | None = None,
    ) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.INFRA_MANAGE)
        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=tenant.organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")
        deleted = await self._cache.invalidate_dataset(
            organization_id=str(tenant.organization_id),
            dataset_id=str(dataset_id),
            version_id=str(version_id) if version_id else None,
        )
        await self._audit.record(
            action=AuditAction.CACHE_INVALIDATED,
            resource_type="dataset",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=dataset_id,
            metadata={"deleted_keys": deleted, "version_id": str(version_id) if version_id else None},
        )
        return {"deleted_keys": deleted}


class GetQueueStatusUseCase:
    def __init__(
        self,
        queue: QueueManager,
        authorization: AuthorizationService,
    ) -> None:
        self._queue = queue
        self._authorization = authorization

    async def execute(self, *, tenant: TenantContext) -> dict[str, Any]:
        self._authorization.require_permission(tenant.role, Permission.INFRA_READ)
        depth = await self._queue.depth()
        return {"queue_depth": depth, "organization_id": str(tenant.organization_id)}
