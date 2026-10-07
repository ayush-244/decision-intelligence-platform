"""IntelligenceReport — persisted data understanding for a DatasetVersion.

Each version may have one report. The report payload is a structured document
covering quality, column intelligence, distributions, correlations, and
analytical readiness. Future modules consume this instead of re-profiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.intelligence_status import IntelligenceReportStatus


@dataclass(frozen=True, slots=True)
class IntelligenceReport:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    status: IntelligenceReportStatus
    quality_score: float | None
    health_score: float | None
    rows_sampled: int
    total_rows: int
    report: dict[str, Any]
    error_message: str | None
    computed_at: datetime | None
    created_at: datetime
    updated_at: datetime
