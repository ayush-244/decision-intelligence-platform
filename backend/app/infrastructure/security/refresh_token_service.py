"""Refresh token lifecycle helpers."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.core.config import Settings
from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.shared.exceptions import AuthenticationError
from app.shared.utils.token_hash import hash_token


class RefreshTokenService:
    """Issue, rotate, and revoke refresh tokens."""

    def __init__(self, settings: Settings, repository: RefreshTokenRepository) -> None:
        self._settings = settings
        self._repository = repository

    def generate_raw_token(self) -> str:
        return secrets.token_urlsafe(48)

    async def issue(
        self, *, user_id: UUID, family_id: UUID | None = None
    ) -> tuple[str, RefreshToken]:
        raw = self.generate_raw_token()
        token_hash = hash_token(raw)
        family = family_id or uuid4()
        expires_at = datetime.now(UTC) + timedelta(days=self._settings.jwt_refresh_token_expire_days)
        record = await self._repository.create(
            user_id=user_id,
            token_hash=token_hash,
            family_id=family,
            expires_at=expires_at,
        )
        return raw, record

    async def rotate(self, raw_token: str) -> tuple[str, RefreshToken, UUID]:
        token_hash = hash_token(raw_token)
        existing = await self._repository.get_by_token_hash(token_hash)
        if existing is None:
            raise AuthenticationError("Invalid refresh token.")
        if existing.revoked_at is not None:
            await self._repository.revoke_family(existing.family_id)
            raise AuthenticationError("Refresh token reuse detected.")
        if existing.expires_at < datetime.now(UTC):
            raise AuthenticationError("Refresh token expired.")
        await self._repository.revoke(existing.id)
        new_raw, new_record = await self.issue(user_id=existing.user_id, family_id=existing.family_id)
        return new_raw, new_record, existing.user_id

    async def revoke_raw(self, raw_token: str) -> None:
        token_hash = hash_token(raw_token)
        existing = await self._repository.get_by_token_hash(token_hash)
        if existing is not None:
            await self._repository.revoke(existing.id)
