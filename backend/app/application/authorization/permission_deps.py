"""FastAPI permission dependency helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.application.authorization.authorization_service import AuthorizationService
from app.domain.value_objects.role import Permission
from app.domain.value_objects.tenant import TenantContext
from app.presentation.api.deps import get_authorization_service, get_tenant_context


def require_permission_dep(permission: Permission):
    """Factory returning a dependency that enforces RBAC before route execution."""

    async def _dependency(
        request: Request,
        tenant: Annotated[TenantContext, Depends(get_tenant_context)],
        authorization: Annotated[AuthorizationService, Depends(get_authorization_service)],
    ) -> TenantContext:
        authorization.require_permission(
            tenant.role,
            permission,
            user_id=tenant.user_id,
            organization_id=tenant.organization_id,
            request_id=_request_id(request),
        )
        return tenant

    return _dependency


def _request_id(request: Request) -> str | None:
    scope_state = request.scope.get("state")
    if isinstance(scope_state, dict):
        value = scope_state.get("request_id")
        return str(value) if value else None
    return None
