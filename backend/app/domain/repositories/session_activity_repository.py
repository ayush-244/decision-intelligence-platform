"""Session activity repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.session_activity import SessionActivity


class SessionActivityRepository(ABC):
    @abstractmethod
    async def append(self, activity: SessionActivity) -> SessionActivity: ...

    @abstractmethod
    async def list_for_session(
        self, *, session_id: UUID, organization_id: UUID, limit: int = 100
    ) -> list[SessionActivity]: ...
