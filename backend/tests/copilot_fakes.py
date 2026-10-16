"""In-memory copilot repositories for API integration tests."""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from app.domain.entities.copilot_conversation import CopilotConversation
from app.domain.entities.copilot_message import CopilotMessage
from app.domain.repositories.copilot_conversation_repository import CopilotConversationRepository
from app.domain.repositories.copilot_message_repository import CopilotMessageRepository
from app.shared.utils.datetime import utc_now


class InMemoryCopilotStore:
    """Process-local store backing fake copilot repository implementations."""

    def __init__(self) -> None:
        self.conversations: dict[UUID, CopilotConversation] = {}
        self.messages: dict[UUID, CopilotMessage] = {}

    def conversation_repo(self) -> FakeCopilotConversationRepository:
        return FakeCopilotConversationRepository(self)

    def message_repo(self) -> FakeCopilotMessageRepository:
        return FakeCopilotMessageRepository(self)


class FakeCopilotConversationRepository(CopilotConversationRepository):
    def __init__(self, store: InMemoryCopilotStore) -> None:
        self._store = store

    async def create(self, conversation: CopilotConversation) -> CopilotConversation:
        self._store.conversations[conversation.id] = conversation
        return conversation

    async def update(self, conversation: CopilotConversation) -> CopilotConversation:
        existing = self._store.conversations.get(conversation.id)
        if existing is None:
            raise KeyError(conversation.id)
        updated = replace(conversation, updated_at=utc_now())
        self._store.conversations[conversation.id] = updated
        return updated

    async def get_by_id(
        self, *, conversation_id: UUID, organization_id: UUID
    ) -> CopilotConversation | None:
        conv = self._store.conversations.get(conversation_id)
        if conv is None or conv.organization_id != organization_id:
            return None
        return conv

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        dataset_id: UUID | None = None,
        limit: int = 50,
    ) -> list[CopilotConversation]:
        rows = [
            c
            for c in self._store.conversations.values()
            if c.organization_id == organization_id
            and (dataset_id is None or c.dataset_id == dataset_id)
        ]
        rows.sort(key=lambda c: c.updated_at, reverse=True)
        return rows[:limit]


class FakeCopilotMessageRepository(CopilotMessageRepository):
    def __init__(self, store: InMemoryCopilotStore) -> None:
        self._store = store

    async def create(self, message: CopilotMessage) -> CopilotMessage:
        self._store.messages[message.id] = message
        return message

    async def list_for_conversation(
        self,
        *,
        conversation_id: UUID,
        organization_id: UUID,
        limit: int = 100,
    ) -> list[CopilotMessage]:
        rows = [
            m
            for m in self._store.messages.values()
            if m.conversation_id == conversation_id and m.organization_id == organization_id
        ]
        rows.sort(key=lambda m: m.created_at)
        return rows[:limit]
