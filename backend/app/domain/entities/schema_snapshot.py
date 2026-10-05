"""SchemaSnapshot — frozen schema at ingest time for a version."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.column_metadata import ColumnMetadata


@dataclass(frozen=True, slots=True)
class SchemaSnapshot:
    id: UUID
    version_id: UUID
    schema_hash: str
    columns: tuple[ColumnMetadata, ...]
    created_at: datetime
