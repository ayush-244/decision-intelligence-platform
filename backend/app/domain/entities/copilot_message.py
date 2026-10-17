"""CopilotMessage — single turn in a copilot conversation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.copilot import MessageRole


@dataclass(frozen=True, slots=True)
class CopilotMessage:
    id: UUID
    conversation_id: UUID
    organization_id: UUID
    role: MessageRole
    content: str
    citations: tuple[dict[str, Any], ...]
    tool_calls: tuple[dict[str, Any], ...]
    context_snapshot: dict[str, Any]
    prompt_version: str
    provider: str
    created_at: datetime
