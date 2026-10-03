"""Membership — links a User to an Organization with a role.

This is the authorization anchor for multi-tenant access. One user may hold
multiple memberships (multiple orgs). Invitations (Phase 2+) will create
memberships with ``invited`` status — schema supports this via ``is_active``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.value_objects.role import MembershipRole


@dataclass(frozen=True, slots=True)
class Membership:
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: MembershipRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
