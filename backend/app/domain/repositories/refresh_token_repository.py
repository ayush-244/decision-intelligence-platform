"""Refresh token repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        family_id: UUID,
        expires_at: object,
    ) -> RefreshToken: ...

    @abstractmethod
    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_id: UUID) -> None: ...

    @abstractmethod
    async def revoke_family(self, family_id: UUID) -> None: ...
