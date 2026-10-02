"""Workspace repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.workspace import Workspace


class WorkspaceRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self, *, workspace_id: UUID, organization_id: UUID
    ) -> Workspace | None: ...

    @abstractmethod
    async def list_for_organization(self, organization_id: UUID) -> list[Workspace]: ...

    @abstractmethod
    async def create(
        self,
        *,
        organization_id: UUID,
        name: str,
        slug: str,
        description: str | None,
    ) -> Workspace: ...

    @abstractmethod
    async def exists_by_name(self, *, organization_id: UUID, name: str) -> bool: ...
