"""Membership repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.membership import Membership
from app.domain.value_objects.role import MembershipRole


class MembershipRepository(ABC):
    @abstractmethod
    async def get_membership(
        self, *, user_id: UUID, organization_id: UUID
    ) -> Membership | None: ...

    @abstractmethod
    async def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        role: MembershipRole,
    ) -> Membership: ...

    @abstractmethod
    async def count_owners(self, organization_id: UUID) -> int: ...
