"""Schema snapshot repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.schema_snapshot import SchemaSnapshot


class SchemaSnapshotRepository(ABC):
    @abstractmethod
    async def create(self, snapshot: SchemaSnapshot) -> SchemaSnapshot: ...

    @abstractmethod
    async def get_by_version(self, *, version_id: UUID) -> SchemaSnapshot | None: ...
