"""Dataset version repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.dataset_version import DatasetVersion


class DatasetVersionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, *, version_id: UUID) -> DatasetVersion | None: ...

    @abstractmethod
    async def list_for_dataset(self, *, dataset_id: UUID) -> list[DatasetVersion]: ...

    @abstractmethod
    async def get_latest(self, *, dataset_id: UUID) -> DatasetVersion | None: ...

    @abstractmethod
    async def next_version_number(self, *, dataset_id: UUID) -> int: ...

    @abstractmethod
    async def create(self, version: DatasetVersion) -> DatasetVersion: ...

    @abstractmethod
    async def find_by_file_hash(
        self, *, organization_id: UUID, file_hash: str
    ) -> DatasetVersion | None: ...
