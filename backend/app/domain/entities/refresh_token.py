"""Refresh token metadata — domain view (never stores raw token)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RefreshToken:
    id: UUID
    user_id: UUID
    family_id: UUID
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None
