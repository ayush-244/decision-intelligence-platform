"""Copilot conversation repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.copilot_conversation import CopilotConversation


class CopilotConversationRepository(ABC):
    @abstractmethod
    async def create(self, conversation: CopilotConversation) -> CopilotConversation: ...

    @abstractmethod
    async def update(self, conversation: CopilotConversation) -> CopilotConversation: ...

    @abstractmethod
    async def get_by_id(
        self, *, conversation_id: UUID, organization_id: UUID
    ) -> CopilotConversation | None: ...

    @abstractmethod
    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        dataset_id: UUID | None = None,
        limit: int = 50,
    ) -> list[CopilotConversation]: ...
