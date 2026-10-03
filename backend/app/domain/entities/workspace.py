"""Workspace — collaboration boundary within an organization.

Groups projects and (future) datasets. Name/slug unique per organization.
Deletion is soft to preserve audit history and allow recovery windows.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Workspace:
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
