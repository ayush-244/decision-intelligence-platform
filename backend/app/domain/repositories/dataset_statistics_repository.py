"""Dataset statistics repository port (profiling placeholder)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.dataset_statistics import DatasetStatistics


class DatasetStatisticsRepository(ABC):
    @abstractmethod
    async def create(self, statistics: DatasetStatistics) -> DatasetStatistics: ...

    @abstractmethod
    async def get_by_version(self, *, version_id: UUID) -> DatasetStatistics | None: ...
