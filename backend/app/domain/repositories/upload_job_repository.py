"""Upload job repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.upload_job import UploadJob
from app.domain.value_objects.dataset_status import UploadJobStatus


class UploadJobRepository(ABC):
    @abstractmethod
    async def create(self, job: UploadJob) -> UploadJob: ...

    @abstractmethod
    async def update_status(
        self,
        *,
        job_id: UUID,
        status: UploadJobStatus,
        version_id: UUID | None = None,
        error_message: str | None = None,
    ) -> None: ...

    @abstractmethod
    async def get_by_id(self, *, job_id: UUID) -> UploadJob | None: ...
