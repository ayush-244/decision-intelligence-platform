"""DecisionSession — links the full analytical journey for a dataset version."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.workspace import DecisionSessionStatus, WorkflowStep


@dataclass(frozen=True, slots=True)
class DecisionSession:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    created_by: UUID
    name: str
    description: str | None
    status: DecisionSessionStatus
    version_number: int
    current_step: WorkflowStep
    statistical_analysis_id: UUID | None
    dag_version_id: UUID | None
    causal_analysis_id: UUID | None
    simulation_run_id: UUID | None
    decision_run_id: UUID | None
    executive_report_id: UUID | None
    workspace_state: dict[str, Any]
    configuration: dict[str, Any]
    paused_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
