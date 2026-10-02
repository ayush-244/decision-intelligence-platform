"""Dataset repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.dataset import Dataset


class DatasetRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self, *, dataset_id: UUID, organization_id: UUID
    ) -> Dataset | None: ...

    @abstractmethod
    async def list_for_project(
        self, *, project_id: UUID, organization_id: UUID
    ) -> list[Dataset]: ...

    @abstractmethod
    async def create(
        self,
        *,
        project_id: UUID,
        organization_id: UUID,
        name: str,
        slug: str,
        description: str | None,
        created_by: UUID,
    ) -> Dataset: ...

    @abstractmethod
    async def update_current_version(
        self, *, dataset_id: UUID, version_id: UUID
    ) -> None: ...

    @abstractmethod
    async def soft_delete(self, *, dataset_id: UUID, organization_id: UUID) -> None: ...

    @abstractmethod
    async def exists_by_name(
        self, *, project_id: UUID, name: str, exclude_id: UUID | None = None
    ) -> bool: ...
