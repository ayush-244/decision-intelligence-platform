"""Copilot ORM ↔ domain mappers."""

from __future__ import annotations

from app.domain.entities.copilot_conversation import CopilotConversation
from app.domain.entities.copilot_message import CopilotMessage
from app.domain.value_objects.copilot import MessageRole
from app.infrastructure.database.models.copilot_conversation import CopilotConversationModel
from app.infrastructure.database.models.copilot_message import CopilotMessageModel


def to_copilot_conversation(model: CopilotConversationModel) -> CopilotConversation:
    pinned = model.pinned_insights_json or []
    return CopilotConversation(
        id=model.id,
        organization_id=model.organization_id,
        created_by=model.created_by,
        dataset_id=model.dataset_id,
        session_id=model.session_id,
        title=model.title,
        context_snapshot=model.context_snapshot_json or {},
        referenced_resources=model.referenced_resources_json or {},
        pinned_insights=tuple(pinned) if isinstance(pinned, list) else (),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_copilot_message(model: CopilotMessageModel) -> CopilotMessage:
    citations = model.citations_json or []
    tools = model.tool_calls_json or []
    return CopilotMessage(
        id=model.id,
        conversation_id=model.conversation_id,
        organization_id=model.organization_id,
        role=MessageRole(model.role),
        content=model.content,
        citations=tuple(citations) if isinstance(citations, list) else (),
        tool_calls=tuple(tools) if isinstance(tools, list) else (),
        context_snapshot=model.context_snapshot_json or {},
        prompt_version=model.prompt_version,
        provider=model.provider,
        created_at=model.created_at,
    )
