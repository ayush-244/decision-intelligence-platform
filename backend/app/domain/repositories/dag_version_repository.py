"""DAG version repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.dag_version import DAGVersion


class DAGVersionRepository(ABC):
    @abstractmethod
    async def create(self, dag: DAGVersion) -> DAGVersion: ...

    @abstractmethod
    async def update(self, dag: DAGVersion) -> DAGVersion: ...

    @abstractmethod
    async def get_by_id(
        self, *, dag_id: UUID, organization_id: UUID
    ) -> DAGVersion | None: ...

    @abstractmethod
    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DAGVersion]: ...

    @abstractmethod
    async def next_version_number(self, *, dataset_id: UUID) -> int: ...
