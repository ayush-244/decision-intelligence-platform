"""AI Copilot API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.application.dto.copilot import CopilotConversationDTO, CopilotMessageDTO


class CreateConversationRequest(BaseModel):
    title: str = Field(default="New conversation", max_length=255)
    dataset_id: str | None = None
    session_id: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)


class CitationResponse(BaseModel):
    resource_type: str
    resource_id: str
    label: str
    excerpt: str


class CopilotMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: list[CitationResponse]
    created_at: str

    @classmethod
    def from_dto(cls, dto: CopilotMessageDTO) -> CopilotMessageResponse:
        return cls(
            id=dto.id,
            role=dto.role,
            content=dto.content,
            citations=[
                CitationResponse(
                    resource_type=c.resource_type,
                    resource_id=c.resource_id,
                    label=c.label,
                    excerpt=c.excerpt,
                )
                for c in dto.citations
            ],
            created_at=dto.created_at,
        )


class CopilotConversationResponse(BaseModel):
    id: str
    title: str
    dataset_id: str | None
    session_id: str | None
    messages: list[CopilotMessageResponse]
    pinned_insights: list[str]
    suggested_questions: list[str]
    context_summary: dict[str, Any]
    created_at: str
    updated_at: str

    @classmethod
    def from_dto(cls, dto: CopilotConversationDTO) -> CopilotConversationResponse:
        return cls(
            id=dto.id,
            title=dto.title,
            dataset_id=dto.dataset_id,
            session_id=dto.session_id,
            messages=[CopilotMessageResponse.from_dto(m) for m in dto.messages],
            pinned_insights=dto.pinned_insights,
            suggested_questions=dto.suggested_questions,
            context_summary=dto.context_summary,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )


class CopilotContextResponse(BaseModel):
    dataset: dict[str, Any]
    data_quality: dict[str, Any]
    statistics: list[dict[str, Any]]
    causal: list[dict[str, Any]]
    simulations: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    reports: list[dict[str, Any]]
    session: dict[str, Any] | None
    prompt_preview: str
