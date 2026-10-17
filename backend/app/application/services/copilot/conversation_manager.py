"""Conversation orchestration — context, LLM, validation, persistence."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

from app.application.dto.copilot import StructuredContext
from app.application.services.copilot.citation_generator import CitationGenerator
from app.application.services.copilot.context_builder import CopilotContextBuilder
from app.application.services.copilot.prompt_composer import CopilotPromptComposer
from app.application.services.copilot.response_validator import CopilotResponseValidator
from app.domain.entities.copilot_conversation import CopilotConversation
from app.domain.entities.copilot_message import CopilotMessage
from app.domain.ports.llm_provider import LlmMessage, LlmProviderPort
from app.domain.repositories.copilot_conversation_repository import CopilotConversationRepository
from app.domain.repositories.copilot_message_repository import CopilotMessageRepository
from app.domain.value_objects.copilot import MessageRole
from app.shared.utils.datetime import utc_now


class CopilotConversationManager:
    """Orchestrate a single copilot turn end-to-end."""

    def __init__(
        self,
        conversations: CopilotConversationRepository,
        messages: CopilotMessageRepository,
        context_builder: CopilotContextBuilder,
        prompt_composer: CopilotPromptComposer,
        validator: CopilotResponseValidator,
        citations: CitationGenerator,
        llm: LlmProviderPort,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._context_builder = context_builder
        self._prompt_composer = prompt_composer
        self._validator = validator
        self._citations = citations
        self._llm = llm

    async def send_message(
        self,
        *,
        conversation: CopilotConversation,
        user_content: str,
        organization_id: UUID,
        user_id: UUID | None,
    ) -> tuple[CopilotMessage, CopilotMessage, CopilotConversation]:
        dataset_id = conversation.dataset_id
        session_id = conversation.session_id

        context = await self._context_builder.build(
            organization_id=organization_id,
            dataset_id=dataset_id,
            session_id=session_id,
        )

        history = await self._messages.list_for_conversation(
            conversation_id=conversation.id,
            organization_id=organization_id,
            limit=20,
        )
        history_text = "\n".join(
            f"{m.role.value}: {m.content[:200]}" for m in history[-6:]
        )

        now = utc_now()
        user_message = CopilotMessage(
            id=uuid4(),
            conversation_id=conversation.id,
            organization_id=organization_id,
            role=MessageRole.USER,
            content=user_content,
            citations=(),
            tool_calls=(),
            context_snapshot={},
            prompt_version=self._prompt_composer.prompt_version,
            provider=self._llm.provider_name,
            created_at=now,
        )
        await self._messages.create(user_message)

        system_prompt = self._prompt_composer.compose_system(context)
        user_prompt = self._prompt_composer.compose_user(
            user_message=user_content, conversation_history=history_text
        )

        from app.domain.ports.llm_provider import LlmCompletionRequest

        llm_response = await self._llm.complete(
            LlmCompletionRequest(
                messages=[LlmMessage(role="user", content=user_prompt)],
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.2,
            )
        )

        validated_content = self._validator.enforce_or_raise(
            content=llm_response.content, context=context
        )
        citation_dtos = self._citations.extract(content=validated_content, context=context)
        if not citation_dtos:
            citation_dtos = self._citations.primary_citations(context)

        citation_dicts = tuple(
            {
                "resource_type": c.resource_type,
                "resource_id": c.resource_id,
                "label": c.label,
                "excerpt": c.excerpt,
            }
            for c in citation_dtos
        )

        assistant_message = CopilotMessage(
            id=uuid4(),
            conversation_id=conversation.id,
            organization_id=organization_id,
            role=MessageRole.ASSISTANT,
            content=validated_content,
            citations=citation_dicts,
            tool_calls=(),
            context_snapshot=_context_to_dict(context),
            prompt_version=self._prompt_composer.prompt_version,
            provider=llm_response.provider,
            created_at=utc_now(),
        )
        await self._messages.create(assistant_message)

        updated_conversation = replace(
            conversation,
            context_snapshot=_context_to_dict(context),
            referenced_resources=_merge_refs(conversation.referenced_resources, citation_dicts),
            updated_at=utc_now(),
        )
        if conversation.title == "New conversation" and user_content:
            updated_conversation = replace(
                updated_conversation,
                title=user_content[:80] + ("…" if len(user_content) > 80 else ""),
            )
        saved = await self._conversations.update(updated_conversation)

        return user_message, assistant_message, saved


def _context_to_dict(ctx: StructuredContext) -> dict[str, Any]:
    return {
        "dataset": ctx.dataset,
        "data_quality": ctx.data_quality,
        "statistics_count": len(ctx.statistics),
        "causal_count": len(ctx.causal),
        "simulations_count": len(ctx.simulations),
        "decisions_count": len(ctx.decisions),
        "reports_count": len(ctx.reports),
    }


def _merge_refs(
    existing: dict[str, list[str]], citations: tuple[dict[str, Any], ...]
) -> dict[str, list[str]]:
    merged = {k: list(v) for k, v in existing.items()}
    for c in citations:
        rtype = c.get("resource_type", "unknown")
        rid = c.get("resource_id", "")
        merged.setdefault(rtype, [])
        if rid and rid not in merged[rtype]:
            merged[rtype].append(rid)
    return merged
