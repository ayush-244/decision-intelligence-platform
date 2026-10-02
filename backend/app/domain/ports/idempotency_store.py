"""Idempotency key store port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IdempotencyStorePort(ABC):
    @abstractmethod
    async def get_response(self, *, key: str, organization_id: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def store_response(
        self,
        *,
        key: str,
        organization_id: str,
        status_code: int,
        body: dict[str, Any],
        ttl_seconds: int,
    ) -> None: ...

    @abstractmethod
    async def claim_key(self, *, key: str, organization_id: str, ttl_seconds: int) -> bool: ...
