"""Project — unit of analytical work within a workspace.

Future datasets, analyses, simulations, and reports attach here. Ownership
chain: Organization → Workspace → Project ensures every artifact is tenant-
scoped.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Project:
    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
