"""AI Decision Copilot endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.application.dto.copilot import CreateConversationRequestDTO, SendMessageRequestDTO
from app.presentation.api.deps import (
    CreateCopilotConversationDep,
    GetCopilotContextDep,
    GetCopilotConversationDep,
    ListCopilotConversationsDep,
    SendCopilotMessageDep,
    TenantContextDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.copilot import (
    CopilotContextResponse,
    CopilotConversationResponse,
    CreateConversationRequest,
    SendMessageRequest,
)

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post(
    "/conversations",
    response_model=DataResponse[CopilotConversationResponse],
    status_code=HTTPStatus.CREATED,
    summary="Create a copilot conversation",
)
async def create_conversation(
    tenant: TenantContextDep,
    use_case: CreateCopilotConversationDep,
    body: CreateConversationRequest,
) -> DataResponse[CopilotConversationResponse]:
    result = await use_case.execute(
        tenant=tenant,
        request=CreateConversationRequestDTO(
            title=body.title,
            dataset_id=body.dataset_id,
            session_id=body.session_id,
        ),
    )
    return DataResponse(data=CopilotConversationResponse.from_dto(result))


@router.get(
    "/conversations",
    response_model=DataResponse[list[CopilotConversationResponse]],
    summary="List copilot conversations",
)
async def list_conversations(
    tenant: TenantContextDep,
    use_case: ListCopilotConversationsDep,
    dataset_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[CopilotConversationResponse]]:
    rows = await use_case.execute(tenant=tenant, dataset_id=dataset_id, limit=limit)
    return DataResponse(data=[CopilotConversationResponse.from_dto(r) for r in rows])


@router.get(
    "/conversations/{conversation_id}",
    response_model=DataResponse[CopilotConversationResponse],
    summary="Get conversation with message history",
)
async def get_conversation(
    tenant: TenantContextDep,
    use_case: GetCopilotConversationDep,
    conversation_id: UUID,
) -> DataResponse[CopilotConversationResponse]:
    result = await use_case.execute(tenant=tenant, conversation_id=conversation_id)
    return DataResponse(data=CopilotConversationResponse.from_dto(result))


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=DataResponse[CopilotConversationResponse],
    summary="Send a message and receive analyst response",
)
async def send_message(
    tenant: TenantContextDep,
    use_case: SendCopilotMessageDep,
    conversation_id: UUID,
    body: SendMessageRequest,
) -> DataResponse[CopilotConversationResponse]:
    result = await use_case.execute(
        tenant=tenant,
        conversation_id=conversation_id,
        request=SendMessageRequestDTO(content=body.content),
    )
    return DataResponse(data=CopilotConversationResponse.from_dto(result))


@router.get(
    "/context",
    response_model=DataResponse[CopilotContextResponse],
    summary="Preview structured analytical context for a dataset",
)
async def get_context(
    tenant: TenantContextDep,
    use_case: GetCopilotContextDep,
    dataset_id: UUID = Query(...),
    session_id: UUID | None = Query(default=None),
) -> DataResponse[CopilotContextResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, session_id=session_id
    )
    return DataResponse(
        data=CopilotContextResponse(
            dataset=payload["dataset"],
            data_quality=payload["data_quality"],
            statistics=payload["statistics"],
            causal=payload["causal"],
            simulations=payload["simulations"],
            decisions=payload["decisions"],
            reports=payload["reports"],
            session=payload["session"],
            prompt_preview=payload["prompt_preview"],
        )
    )
