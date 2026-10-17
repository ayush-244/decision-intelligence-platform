"""CopilotConversation — persisted AI analyst session."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CopilotConversation:
    id: UUID
    organization_id: UUID
    created_by: UUID | None
    dataset_id: UUID | None
    session_id: UUID | None
    title: str
    context_snapshot: dict[str, Any]
    referenced_resources: dict[str, list[str]]
    pinned_insights: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
