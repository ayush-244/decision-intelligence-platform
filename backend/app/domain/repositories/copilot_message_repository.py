"""Copilot message repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.copilot_message import CopilotMessage


class CopilotMessageRepository(ABC):
    @abstractmethod
    async def create(self, message: CopilotMessage) -> CopilotMessage: ...

    @abstractmethod
    async def list_for_conversation(
        self,
        *,
        conversation_id: UUID,
        organization_id: UUID,
        limit: int = 100,
    ) -> list[CopilotMessage]: ...
