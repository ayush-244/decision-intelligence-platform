"""In-memory idempotency store for tests."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    status_code: int
    body: dict[str, Any]
    expires_at: float
    in_flight: bool = False


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._data: dict[str, _Entry] = {}

    def _key(self, *, key: str, organization_id: str) -> str:
        return f"{organization_id}:{key}"

    async def get_response(self, *, key: str, organization_id: str) -> dict[str, Any] | None:
        entry = self._data.get(self._key(key=key, organization_id=organization_id))
        if entry is None or entry.expires_at <= time.monotonic():
            return None
        if entry.in_flight:
            return None
        return {"status_code": entry.status_code, "body": entry.body}

    async def store_response(
        self,
        *,
        key: str,
        organization_id: str,
        status_code: int,
        body: dict[str, Any],
        ttl_seconds: int,
    ) -> None:
        composite = self._key(key=key, organization_id=organization_id)
        self._data[composite] = _Entry(
            status_code=status_code,
            body=body,
            expires_at=time.monotonic() + ttl_seconds,
            in_flight=False,
        )

    async def claim_key(self, *, key: str, organization_id: str, ttl_seconds: int) -> bool:
        composite = self._key(key=key, organization_id=organization_id)
        existing = self._data.get(composite)
        if existing and existing.expires_at > time.monotonic():
            if existing.in_flight:
                return False
            if existing.body:
                return False
        self._data[composite] = _Entry(
            status_code=0,
            body={},
            expires_at=time.monotonic() + ttl_seconds,
            in_flight=True,
        )
        return True
