"""Centralized authorization — the only place role checks should occur."""

from __future__ import annotations

from uuid import UUID

from app.core.logging import get_logger
from app.domain.value_objects.role import ROLE_PERMISSIONS, MembershipRole, Permission
from app.shared.exceptions import ForbiddenError

_logger = get_logger(__name__)


class AuthorizationService:
    """Evaluate RBAC permissions for organization-scoped operations."""

    def require_permission(
        self,
        role: MembershipRole,
        permission: Permission,
        *,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        request_id: str | None = None,
    ) -> None:
        allowed = ROLE_PERMISSIONS.get(role, frozenset())
        if permission not in allowed:
            _logger.warning(
                "authorization_denied",
                permission=permission.value,
                role=role.value,
                user_id=str(user_id) if user_id else None,
                organization_id=str(organization_id) if organization_id else None,
                request_id=request_id,
            )
            raise ForbiddenError(
                "You do not have permission to perform this action.",
                details={"permission": permission.value},
            )

    def has_permission(self, role: MembershipRole, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(role, frozenset())
