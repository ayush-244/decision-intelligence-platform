"""DatasetStatistics — placeholder for profiling metrics (Phase 4+).

Stored now so profiling modules can populate without migrations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DatasetStatistics:
    id: UUID
    version_id: UUID
    metrics: dict[str, Any]
    created_at: datetime
