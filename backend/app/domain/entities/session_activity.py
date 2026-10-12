"""SessionActivity — chronological workspace events and collaboration foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.workspace import SessionActivityType


@dataclass(frozen=True, slots=True)
class SessionActivity:
    id: UUID
    session_id: UUID
    organization_id: UUID
    user_id: UUID | None
    activity_type: SessionActivityType
    title: str
    description: str | None
    resource_type: str | None
    resource_id: UUID | None
    metadata: dict[str, Any]
    created_at: datetime
