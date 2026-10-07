"""ValidationReport — structured outcome of file validation checks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.dataset_status import ValidationStatus


@dataclass(frozen=True, slots=True)
class ValidationReport:
    id: UUID
    version_id: UUID
    status: ValidationStatus
    checks: dict[str, Any]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    created_at: datetime
