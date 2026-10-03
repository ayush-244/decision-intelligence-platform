"""Tenant context carried through use-cases for row-level isolation.

Every organization-scoped operation receives a TenantContext so repositories
can enforce ``organization_id`` filters consistently. This is the foundation
for multi-tenant query isolation at scale.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.domain.value_objects.role import MembershipRole


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Resolved tenant scope for the current request."""

    user_id: UUID
    organization_id: UUID
    role: MembershipRole

    # Optional drill-down scope (set when operating within a workspace/project).
    workspace_id: UUID | None = None
    project_id: UUID | None = None
