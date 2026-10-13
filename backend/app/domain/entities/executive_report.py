"""ExecutiveReport — versioned executive intelligence artifact."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.executive import ExecutiveReportStatus


@dataclass(frozen=True, slots=True)
class ExecutiveReport:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    decision_run_id: UUID | None
    created_by: UUID
    status: ExecutiveReportStatus
    name: str
    business_objective: str
    version_number: int
    configuration: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    executed_at: datetime | None
    created_at: datetime
    updated_at: datetime
