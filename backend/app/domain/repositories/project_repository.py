"""Project repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.project import Project


class ProjectRepository(ABC):
    @abstractmethod
    async def get_by_id(self, *, project_id: UUID, workspace_id: UUID) -> Project | None: ...

    @abstractmethod
    async def list_for_workspace(self, workspace_id: UUID) -> list[Project]: ...

    @abstractmethod
    async def create(
        self,
        *,
        workspace_id: UUID,
        name: str,
        slug: str,
        description: str | None,
    ) -> Project: ...

    @abstractmethod
    async def exists_by_name(self, *, workspace_id: UUID, name: str) -> bool: ...

    @abstractmethod
    async def get_workspace_id(self, project_id: UUID) -> UUID | None: ...
