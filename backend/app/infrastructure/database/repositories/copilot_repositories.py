"""SQLAlchemy copilot repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.copilot_conversation import CopilotConversation
from app.domain.entities.copilot_message import CopilotMessage
from app.domain.repositories.copilot_conversation_repository import CopilotConversationRepository
from app.domain.repositories.copilot_message_repository import CopilotMessageRepository
from app.infrastructure.database.mappers.copilot import to_copilot_conversation, to_copilot_message
from app.infrastructure.database.models.copilot_conversation import CopilotConversationModel
from app.infrastructure.database.models.copilot_message import CopilotMessageModel


class SqlAlchemyCopilotConversationRepository(CopilotConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, conversation: CopilotConversation) -> CopilotConversation:
        model = CopilotConversationModel(
            id=conversation.id,
            organization_id=conversation.organization_id,
            created_by=conversation.created_by,
            dataset_id=conversation.dataset_id,
            session_id=conversation.session_id,
            title=conversation.title,
            context_snapshot_json=conversation.context_snapshot,
            referenced_resources_json=conversation.referenced_resources,
            pinned_insights_json=list(conversation.pinned_insights),
        )
        self._session.add(model)
        await self._session.flush()
        return to_copilot_conversation(model)

    async def update(self, conversation: CopilotConversation) -> CopilotConversation:
        result = await self._session.execute(
            select(CopilotConversationModel).where(CopilotConversationModel.id == conversation.id)
        )
        model = result.scalar_one()
        model.title = conversation.title
        model.context_snapshot_json = conversation.context_snapshot
        model.referenced_resources_json = conversation.referenced_resources
        model.pinned_insights_json = list(conversation.pinned_insights)
        await self._session.flush()
        return to_copilot_conversation(model)

    async def get_by_id(
        self, *, conversation_id: UUID, organization_id: UUID
    ) -> CopilotConversation | None:
        result = await self._session.execute(
            select(CopilotConversationModel).where(
                CopilotConversationModel.id == conversation_id,
                CopilotConversationModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_copilot_conversation(model) if model else None

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        dataset_id: UUID | None = None,
        limit: int = 50,
    ) -> list[CopilotConversation]:
        stmt = (
            select(CopilotConversationModel)
            .where(CopilotConversationModel.organization_id == organization_id)
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
        )
        if dataset_id is not None:
            stmt = stmt.where(CopilotConversationModel.dataset_id == dataset_id)
        result = await self._session.execute(stmt)
        return [to_copilot_conversation(m) for m in result.scalars()]


class SqlAlchemyCopilotMessageRepository(CopilotMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, message: CopilotMessage) -> CopilotMessage:
        model = CopilotMessageModel(
            id=message.id,
            conversation_id=message.conversation_id,
            organization_id=message.organization_id,
            role=message.role.value,
            content=message.content,
            citations_json=list(message.citations),
            tool_calls_json=list(message.tool_calls),
            context_snapshot_json=message.context_snapshot,
            prompt_version=message.prompt_version,
            provider=message.provider,
        )
        self._session.add(model)
        await self._session.flush()
        return to_copilot_message(model)

    async def list_for_conversation(
        self,
        *,
        conversation_id: UUID,
        organization_id: UUID,
        limit: int = 100,
    ) -> list[CopilotMessage]:
        result = await self._session.execute(
            select(CopilotMessageModel)
            .where(
                CopilotMessageModel.conversation_id == conversation_id,
                CopilotMessageModel.organization_id == organization_id,
            )
            .order_by(CopilotMessageModel.created_at.asc())
            .limit(limit)
        )
        return [to_copilot_message(m) for m in result.scalars()]
