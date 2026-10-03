"""Intelligence report lifecycle status."""

from __future__ import annotations

from enum import StrEnum


class IntelligenceReportStatus(StrEnum):
    """Computation state for a version-scoped intelligence report."""

    PENDING = "pending"
    COMPUTING = "computing"
    COMPLETED = "completed"
    FAILED = "failed"
