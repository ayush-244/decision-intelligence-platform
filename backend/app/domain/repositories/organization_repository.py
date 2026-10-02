"""Organization repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.organization import Organization


class OrganizationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, organization_id: UUID) -> Organization | None: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Organization | None: ...

    @abstractmethod
    async def list_for_user(self, user_id: UUID) -> list[Organization]: ...

    @abstractmethod
    async def create(self, *, name: str, slug: str) -> Organization: ...
