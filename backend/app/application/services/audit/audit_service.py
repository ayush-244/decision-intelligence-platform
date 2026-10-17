"""Central audit service — immutable append-only security event log."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.value_objects.audit_action import AuditAction

_logger = get_logger(__name__)


class AuditService:
    """Records security-relevant actions with structured metadata and request correlation."""

    def __init__(self, repository: AuditLogRepository) -> None:
        self._repository = repository

    async def record(
        self,
        *,
        action: AuditAction | str,
        resource_type: str,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        resource_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> None:
        action_str = action.value if isinstance(action, AuditAction) else action
        enriched = dict(metadata or {})
        if request_id:
            enriched["request_id"] = request_id

        await self._repository.append(
            action=action_str,
            resource_type=resource_type,
            user_id=user_id,
            organization_id=organization_id,
            resource_id=resource_id,
            metadata=enriched,
        )
        _logger.info(
            "audit_event",
            audit_action=action_str,
            resource_type=resource_type,
            user_id=str(user_id) if user_id else None,
            organization_id=str(organization_id) if organization_id else None,
            request_id=request_id,
        )

    async def record_authorization_denied(
        self,
        *,
        user_id: UUID | None,
        organization_id: UUID | None,
        permission: str,
        resource_type: str,
        request_id: str | None = None,
    ) -> None:
        await self.record(
            action=AuditAction.AUTHORIZATION_DENIED,
            resource_type=resource_type,
            user_id=user_id,
            organization_id=organization_id,
            metadata={"permission": permission},
            request_id=request_id,
        )
        _logger.warning(
            "authorization_denied",
            permission=permission,
            resource_type=resource_type,
            user_id=str(user_id) if user_id else None,
            request_id=request_id,
        )
