"""User entity — platform identity.

Exists independently of organizations. A user gains access to tenant resources
only through Membership records. Password hash never leaves infrastructure;
domain stores only the fact that credentials exist.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class User:
    id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
