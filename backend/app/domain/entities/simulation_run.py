"""SimulationRun — persisted counterfactual simulation anchored to causal models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.simulation import SimulationRunStatus


@dataclass(frozen=True, slots=True)
class SimulationRun:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    causal_analysis_id: UUID
    statistical_analysis_id: UUID | None
    scenario_id: UUID
    created_by: UUID
    status: SimulationRunStatus
    name: str
    configuration: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    executed_at: datetime | None
    created_at: datetime
    updated_at: datetime
