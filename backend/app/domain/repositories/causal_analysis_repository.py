"""Causal analysis repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.causal_analysis import CausalAnalysisRun


class CausalAnalysisRepository(ABC):
    @abstractmethod
    async def create(self, run: CausalAnalysisRun) -> CausalAnalysisRun: ...

    @abstractmethod
    async def update(self, run: CausalAnalysisRun) -> CausalAnalysisRun: ...

    @abstractmethod
    async def get_by_id(
        self, *, analysis_id: UUID, organization_id: UUID
    ) -> CausalAnalysisRun | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[CausalAnalysisRun]: ...

    @abstractmethod
    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[CausalAnalysisRun]: ...
