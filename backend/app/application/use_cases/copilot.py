"""AI Copilot use cases."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.application.authorization.authorization_service import AuthorizationService
from app.application.dto.copilot import (
    CitationDTO,
    CopilotConversationDTO,
    CopilotMessageDTO,
    CreateConversationRequestDTO,
    SendMessageRequestDTO,
)
from app.application.services.audit.audit_service import AuditService
from app.application.services.copilot.context_builder import CopilotContextBuilder
from app.application.services.copilot.conversation_manager import CopilotConversationManager
from app.domain.entities.copilot_conversation import CopilotConversation
from app.domain.repositories.copilot_conversation_repository import CopilotConversationRepository
from app.domain.repositories.copilot_message_repository import CopilotMessageRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.value_objects.audit_action import AuditAction
from app.domain.value_objects.copilot import SUGGESTED_QUESTIONS
from app.domain.value_objects.role import Permission
from app.domain.value_objects.tenant import TenantContext
from app.shared.exceptions import NotFoundError
from app.shared.utils.datetime import utc_now


def _to_message_dto(message) -> CopilotMessageDTO:
    return CopilotMessageDTO(
        id=str(message.id),
        role=message.role.value,
        content=message.content,
        citations=[
            CitationDTO(
                resource_type=c.get("resource_type", ""),
                resource_id=c.get("resource_id", ""),
                label=c.get("label", ""),
                excerpt=c.get("excerpt", ""),
            )
            for c in message.citations
        ],
        created_at=message.created_at.isoformat(),
    )


class CreateCopilotConversationUseCase:
    def __init__(
        self,
        conversations: CopilotConversationRepository,
        datasets: DatasetRepository,
        authorization: AuthorizationService,
        audit: AuditService,
    ) -> None:
        self._conversations = conversations
        self._datasets = datasets
        self._authorization = authorization
        self._audit = audit

    async def execute(
        self,
        *,
        tenant: TenantContext,
        request: CreateConversationRequestDTO,
    ) -> CopilotConversationDTO:
        self._authorization.require_permission(tenant.role, Permission.COPILOT_CREATE)
        dataset_id = UUID(request.dataset_id) if request.dataset_id else None
        session_id = UUID(request.session_id) if request.session_id else None
        if dataset_id:
            ds = await self._datasets.get_by_id(
                dataset_id=dataset_id, organization_id=tenant.organization_id
            )
            if ds is None:
                raise NotFoundError("Dataset not found.")
        now = utc_now()
        conv = CopilotConversation(
            id=uuid4(),
            organization_id=tenant.organization_id,
            created_by=tenant.user_id,
            dataset_id=dataset_id,
            session_id=session_id,
            title=request.title or "New conversation",
            context_snapshot={},
            referenced_resources={},
            pinned_insights=(),
            created_at=now,
            updated_at=now,
        )
        created = await self._conversations.create(conv)
        await self._audit.record(
            action=AuditAction.COPILOT_CONVERSATION_CREATED,
            resource_type="copilot_conversation",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=created.id,
        )
        return CopilotConversationDTO(
            id=str(created.id),
            title=created.title,
            dataset_id=str(created.dataset_id) if created.dataset_id else None,
            session_id=str(created.session_id) if created.session_id else None,
            messages=[],
            pinned_insights=list(created.pinned_insights),
            suggested_questions=list(SUGGESTED_QUESTIONS),
            context_summary=created.context_snapshot,
            created_at=created.created_at.isoformat(),
            updated_at=created.updated_at.isoformat(),
        )


class SendCopilotMessageUseCase:
    def __init__(
        self,
        conversations: CopilotConversationRepository,
        messages: CopilotMessageRepository,
        manager: CopilotConversationManager,
        authorization: AuthorizationService,
        audit: AuditService,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._manager = manager
        self._authorization = authorization
        self._audit = audit

    async def execute(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
        request: SendMessageRequestDTO,
    ) -> CopilotConversationDTO:
        self._authorization.require_permission(tenant.role, Permission.COPILOT_CREATE)
        conv = await self._conversations.get_by_id(
            conversation_id=conversation_id, organization_id=tenant.organization_id
        )
        if conv is None:
            raise NotFoundError("Conversation not found.")
        _, assistant, updated = await self._manager.send_message(
            conversation=conv,
            user_content=request.content,
            organization_id=tenant.organization_id,
            user_id=tenant.user_id,
        )
        await self._audit.record(
            action=AuditAction.COPILOT_MESSAGE_SENT,
            resource_type="copilot_conversation",
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            resource_id=conversation_id,
            metadata={"provider": assistant.provider, "prompt_version": assistant.prompt_version},
        )
        return await _load_conversation_dto(
            self._conversations, self._messages, updated, tenant.organization_id
        )


class GetCopilotConversationUseCase:
    def __init__(
        self,
        conversations: CopilotConversationRepository,
        messages: CopilotMessageRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._conversations = conversations
        self._messages = messages
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        conversation_id: UUID,
    ) -> CopilotConversationDTO:
        self._authorization.require_permission(tenant.role, Permission.COPILOT_READ)
        conv = await self._conversations.get_by_id(
            conversation_id=conversation_id, organization_id=tenant.organization_id
        )
        if conv is None:
            raise NotFoundError("Conversation not found.")
        return await _load_conversation_dto(
            self._conversations, self._messages, conv, tenant.organization_id
        )


class ListCopilotConversationsUseCase:
    def __init__(
        self,
        conversations: CopilotConversationRepository,
        authorization: AuthorizationService,
    ) -> None:
        self._conversations = conversations
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID | None = None,
        limit: int = 50,
    ) -> list[CopilotConversationDTO]:
        self._authorization.require_permission(tenant.role, Permission.COPILOT_READ)
        rows = await self._conversations.list_for_organization(
            organization_id=tenant.organization_id,
            dataset_id=dataset_id,
            limit=limit,
        )
        return [
            CopilotConversationDTO(
                id=str(c.id),
                title=c.title,
                dataset_id=str(c.dataset_id) if c.dataset_id else None,
                session_id=str(c.session_id) if c.session_id else None,
                messages=[],
                pinned_insights=list(c.pinned_insights),
                suggested_questions=list(SUGGESTED_QUESTIONS),
                context_summary=c.context_snapshot,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in rows
        ]


class GetCopilotContextUseCase:
    def __init__(
        self,
        context_builder: CopilotContextBuilder,
        authorization: AuthorizationService,
    ) -> None:
        self._context_builder = context_builder
        self._authorization = authorization

    async def execute(
        self,
        *,
        tenant: TenantContext,
        dataset_id: UUID,
        session_id: UUID | None = None,
    ) -> dict:
        self._authorization.require_permission(tenant.role, Permission.COPILOT_READ)
        ctx = await self._context_builder.build(
            organization_id=tenant.organization_id,
            dataset_id=dataset_id,
            session_id=session_id,
        )
        return {
            "dataset": ctx.dataset,
            "data_quality": ctx.data_quality,
            "statistics": ctx.statistics,
            "causal": ctx.causal,
            "simulations": ctx.simulations,
            "decisions": ctx.decisions,
            "reports": ctx.reports,
            "session": ctx.session,
            "prompt_preview": ctx.to_prompt_sections(),
        }


async def _load_conversation_dto(
    conversations: CopilotConversationRepository,
    messages_repo: CopilotMessageRepository | None,
    conv: CopilotConversation,
    organization_id: UUID,
) -> CopilotConversationDTO:
    messages = []
    if messages_repo:
        rows = await messages_repo.list_for_conversation(
            conversation_id=conv.id, organization_id=organization_id
        )
        messages = [_to_message_dto(m) for m in rows]
    return CopilotConversationDTO(
        id=str(conv.id),
        title=conv.title,
        dataset_id=str(conv.dataset_id) if conv.dataset_id else None,
        session_id=str(conv.session_id) if conv.session_id else None,
        messages=messages,
        pinned_insights=list(conv.pinned_insights),
        suggested_questions=list(SUGGESTED_QUESTIONS),
        context_summary=conv.context_snapshot,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )
