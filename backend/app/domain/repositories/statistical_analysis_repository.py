"""Statistical analysis repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.statistical_analysis import StatisticalAnalysisRun


class StatisticalAnalysisRepository(ABC):
    @abstractmethod
    async def create(self, run: StatisticalAnalysisRun) -> StatisticalAnalysisRun: ...

    @abstractmethod
    async def update(self, run: StatisticalAnalysisRun) -> StatisticalAnalysisRun: ...

    @abstractmethod
    async def get_by_id(
        self, *, analysis_id: UUID, organization_id: UUID
    ) -> StatisticalAnalysisRun | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[StatisticalAnalysisRun]: ...

    @abstractmethod
    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[StatisticalAnalysisRun]: ...
