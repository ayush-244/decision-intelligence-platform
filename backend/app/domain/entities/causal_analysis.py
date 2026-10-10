"""CausalAnalysisRun — persisted, versioned causal inference analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.causal import CausalEstimatorType, CausalRunStatus


@dataclass(frozen=True, slots=True)
class CausalAnalysisRun:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    dag_version_id: UUID | None
    created_by: UUID
    status: CausalRunStatus
    treatment: str
    outcome: str
    estimator: CausalEstimatorType | None
    configuration: dict[str, Any]
    result: dict[str, Any]
    error_message: str | None
    executed_at: datetime | None
    created_at: datetime
    updated_at: datetime
