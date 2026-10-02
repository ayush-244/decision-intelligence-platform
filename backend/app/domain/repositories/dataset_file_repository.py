"""Dataset file repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.dataset_file import DatasetFile


class DatasetFileRepository(ABC):
    @abstractmethod
    async def create(self, file: DatasetFile) -> DatasetFile: ...

    @abstractmethod
    async def get_by_version(self, *, version_id: UUID) -> DatasetFile | None: ...
