"""Decision run repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.decision_run import DecisionRun


class DecisionRunRepository(ABC):
    @abstractmethod
    async def create(self, run: DecisionRun) -> DecisionRun: ...

    @abstractmethod
    async def update(self, run: DecisionRun) -> DecisionRun: ...

    @abstractmethod
    async def get_by_id(
        self, *, decision_id: UUID, organization_id: UUID
    ) -> DecisionRun | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionRun]: ...

    @abstractmethod
    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionRun]: ...
