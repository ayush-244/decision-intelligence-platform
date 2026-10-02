"""Analytics job repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.analytics_job import AnalyticsJob
from app.domain.value_objects.infrastructure import JobStatus, JobType


class AnalyticsJobRepository(ABC):
    @abstractmethod
    async def create(self, job: AnalyticsJob) -> AnalyticsJob: ...

    @abstractmethod
    async def update(self, job: AnalyticsJob) -> AnalyticsJob: ...

    @abstractmethod
    async def get_by_id(
        self, *, job_id: UUID, organization_id: UUID
    ) -> AnalyticsJob | None: ...

    @abstractmethod
    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        status: JobStatus | None = None,
        job_type: JobType | None = None,
        limit: int = 50,
    ) -> list[AnalyticsJob]: ...

    @abstractmethod
    async def list_running(self, *, limit: int = 20) -> list[AnalyticsJob]: ...

    @abstractmethod
    async def get_by_id_any(self, *, job_id: UUID) -> AnalyticsJob | None: ...
