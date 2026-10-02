"""Decision session repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.decision_session import DecisionSession


class DecisionSessionRepository(ABC):
    @abstractmethod
    async def create(self, session: DecisionSession) -> DecisionSession: ...

    @abstractmethod
    async def update(self, session: DecisionSession) -> DecisionSession: ...

    @abstractmethod
    async def get_by_id(
        self, *, session_id: UUID, organization_id: UUID
    ) -> DecisionSession | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionSession]: ...

    @abstractmethod
    async def search_by_name(
        self, *, organization_id: UUID, query: str, limit: int = 20
    ) -> list[DecisionSession]: ...

    @abstractmethod
    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int: ...
