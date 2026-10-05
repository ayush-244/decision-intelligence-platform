"""Dataset — logical container for versioned tabular data within a project.

A Dataset is the stable identity users see in the UI. Immutable analytical
snapshots live in DatasetVersion rows. Future analyses MUST reference a
DatasetVersion, not this entity, to guarantee reproducibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Dataset:
    id: UUID
    project_id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    created_by: UUID
    current_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
