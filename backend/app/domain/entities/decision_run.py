"""DecisionRun — persisted decision intelligence analysis with ranked recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.decision import DecisionRunStatus


@dataclass(frozen=True, slots=True)
class DecisionRun:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    created_by: UUID
    status: DecisionRunStatus
    name: str
    primary_objective: str
    configuration: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    executed_at: datetime | None
    created_at: datetime
    updated_at: datetime
