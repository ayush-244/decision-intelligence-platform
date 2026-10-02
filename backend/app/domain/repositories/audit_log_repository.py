"""Audit log repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from app.domain.entities.audit_log import AuditLog


class AuditLogRepository(ABC):
    @abstractmethod
    async def append(
        self,
        *,
        action: str,
        resource_type: str,
        user_id: UUID | None = None,
        organization_id: UUID | None = None,
        resource_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog: ...

    @abstractmethod
    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int = 50,
        resource_type: str | None = None,
    ) -> list[AuditLog]: ...
