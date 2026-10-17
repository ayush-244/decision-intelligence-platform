"""Audit log entry — append-only record of security-relevant actions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AuditLog:
    id: UUID
    action: str
    resource_type: str
    user_id: UUID | None
    organization_id: UUID | None
    resource_id: UUID | None
    metadata: dict[str, Any]
    created_at: datetime
