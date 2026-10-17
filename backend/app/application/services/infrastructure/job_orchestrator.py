"""Job submission, lifecycle, and queue orchestration."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.application.dto.infrastructure import SubmitJobRequestDTO
from app.domain.entities.analytics_job import AnalyticsJob
from app.domain.ports.job_queue import JobQueuePort
from app.domain.repositories.analytics_job_repository import AnalyticsJobRepository
from app.domain.value_objects.infrastructure import JobStatus, JobType
from app.shared.exceptions import BusinessValidationError, NotFoundError
from app.shared.utils.datetime import utc_now


class JobOrchestrator:
    """Enqueue and manage analytics background jobs."""

    def __init__(
        self,
        jobs: AnalyticsJobRepository,
        queue: JobQueuePort,
        max_retries: int = 3,
    ) -> None:
        self._jobs = jobs
        self._queue = queue
        self._max_retries = max_retries

    async def submit(
        self,
        *,
        organization_id: UUID,
        created_by: UUID | None,
        request: SubmitJobRequestDTO,
    ) -> AnalyticsJob:
        now = utc_now()
        try:
            job_type = JobType(request.job_type)
        except ValueError as exc:
            raise BusinessValidationError(
                f"Unknown job type: {request.job_type}", code="invalid_job_type"
            ) from exc

        job = AnalyticsJob(
            id=uuid4(),
            organization_id=organization_id,
            created_by=created_by,
            job_type=job_type,
            status=JobStatus.QUEUED,
            dataset_id=UUID(request.dataset_id) if request.dataset_id else None,
            version_id=UUID(request.version_id) if request.version_id else None,
            resource_type=request.resource_type,
            resource_id=UUID(request.resource_id) if request.resource_id else None,
            name=request.name,
            configuration=request.configuration,
            result={},
            progress=0,
            error_message=None,
            retry_count=0,
            max_retries=self._max_retries,
            logs=(f"Job queued at {now.isoformat()}",),
            estimated_duration_ms=self._estimate_duration(job_type),
            queued_at=now,
            started_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        created = await self._jobs.create(job)
        await self._queue.enqueue(job_id=created.id)
        return created

    async def cancel(self, *, job: AnalyticsJob) -> AnalyticsJob:
        if job.status in {JobStatus.COMPLETED, JobStatus.CANCELLED}:
            raise BusinessValidationError("Job cannot be cancelled.", code="job_not_cancellable")
        now = utc_now()
        cancelled = self._replace(
            job,
            status=JobStatus.CANCELLED,
            completed_at=now,
            logs=job.logs + (f"Cancelled at {now.isoformat()}",),
        )
        await self._queue.remove(job_id=job.id)
        return await self._jobs.update(cancelled)

    async def retry(self, *, job: AnalyticsJob) -> AnalyticsJob:
        if job.status not in {JobStatus.FAILED, JobStatus.CANCELLED}:
            raise BusinessValidationError("Only failed jobs can be retried.", code="job_not_retryable")
        if job.retry_count >= job.max_retries:
            raise BusinessValidationError("Max retries exceeded.", code="max_retries")
        now = utc_now()
        retried = self._replace(
            job,
            status=JobStatus.RETRYING,
            progress=0,
            error_message=None,
            retry_count=job.retry_count + 1,
            started_at=None,
            completed_at=None,
            logs=job.logs + (f"Retry #{job.retry_count + 1} at {now.isoformat()}",),
        )
        updated = await self._jobs.update(retried)
        await self._queue.enqueue(job_id=updated.id)
        return updated

    async def get(self, *, job_id: UUID, organization_id: UUID) -> AnalyticsJob:
        job = await self._jobs.get_by_id(job_id=job_id, organization_id=organization_id)
        if job is None:
            raise NotFoundError("Job not found.")
        return job

    @staticmethod
    def _estimate_duration(job_type: JobType) -> int:
        return {
            JobType.DATASET_PROCESSING: 30_000,
            JobType.DATA_INTELLIGENCE: 45_000,
            JobType.STATISTICS: 60_000,
            JobType.CAUSAL_ANALYSIS: 90_000,
            JobType.SIMULATION: 120_000,
            JobType.DECISION: 60_000,
            JobType.EXECUTIVE_REPORT: 45_000,
        }.get(job_type, 60_000)

    @staticmethod
    def _replace(job: AnalyticsJob, **changes: Any) -> AnalyticsJob:
        from dataclasses import replace

        return replace(job, updated_at=utc_now(), **changes)
