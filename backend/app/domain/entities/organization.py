"""Organization — top-level tenant boundary.

All billable / isolatable resources ultimately belong to an organization.
Users access organizations through Membership. Workspaces partition work
within an org (like GitHub org → teams/spaces or Notion workspace).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Organization:
    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
