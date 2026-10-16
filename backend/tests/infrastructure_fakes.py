"""In-memory infrastructure fakes for tests."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from app.domain.entities.analytics_job import AnalyticsJob
from app.domain.repositories.analytics_job_repository import AnalyticsJobRepository
from app.domain.value_objects.infrastructure import JobStatus, JobType
from app.infrastructure.cache.in_memory_cache_store import InMemoryCacheStore
from app.infrastructure.queue.in_memory_job_queue import InMemoryJobQueue
from app.shared.utils.datetime import utc_now


class InMemoryInfrastructureStore:
    """Process-local store for analytics jobs, queue, and cache."""

    def __init__(self) -> None:
        self.jobs: dict[UUID, AnalyticsJob] = {}
        self.queue = InMemoryJobQueue()
        self.cache = InMemoryCacheStore()

    def job_repo(self) -> FakeAnalyticsJobRepository:
        return FakeAnalyticsJobRepository(self)


class FakeAnalyticsJobRepository(AnalyticsJobRepository):
    def __init__(self, store: InMemoryInfrastructureStore) -> None:
        self._store = store

    async def create(self, job: AnalyticsJob) -> AnalyticsJob:
        self._store.jobs[job.id] = job
        return job

    async def update(self, job: AnalyticsJob) -> AnalyticsJob:
        updated = replace(job, updated_at=utc_now())
        self._store.jobs[job.id] = updated
        return updated

    async def get_by_id(
        self, *, job_id: UUID, organization_id: UUID
    ) -> AnalyticsJob | None:
        job = self._store.jobs.get(job_id)
        if job is None or job.organization_id != organization_id:
            return None
        return job

    async def get_by_id_any(self, *, job_id: UUID) -> AnalyticsJob | None:
        return self._store.jobs.get(job_id)

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        status: JobStatus | None = None,
        job_type: JobType | None = None,
        limit: int = 50,
    ) -> list[AnalyticsJob]:
        rows = [
            j
            for j in self._store.jobs.values()
            if j.organization_id == organization_id
            and (status is None or j.status == status)
            and (job_type is None or j.job_type == job_type)
        ]
        rows.sort(key=lambda j: j.queued_at, reverse=True)
        return rows[:limit]

    async def list_running(self, *, limit: int = 20) -> list[AnalyticsJob]:
        rows = [j for j in self._store.jobs.values() if j.status == JobStatus.RUNNING]
        return rows[:limit]
