"""StatisticalAnalysisRun — persisted, versioned statistical analysis.

Each run captures configuration, assumption checks, test execution, effect
sizes, confidence intervals, and business interpretation. Future causal,
simulation, and reporting modules reference AnalysisRun.id for reproducibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.statistics import AnalysisRunStatus, StatisticalTestType


@dataclass(frozen=True, slots=True)
class StatisticalAnalysisRun:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    created_by: UUID
    status: AnalysisRunStatus
    goal: str
    test_type: StatisticalTestType | None
    configuration: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    executed_at: datetime | None
    created_at: datetime
    updated_at: datetime
