"""SimulationScenario — versioned business scenario for counterfactual simulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SimulationScenario:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    created_by: UUID
    name: str
    description: str | None
    objective: str | None
    notes: str | None
    is_baseline: bool
    interventions: list[dict[str, Any]]
    constraints: list[dict[str, Any]]
    version_number: int
    parent_scenario_id: UUID | None
    created_at: datetime
    updated_at: datetime
