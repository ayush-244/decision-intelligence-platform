"""In-memory cache store for tests and local development without Redis."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _Entry:
    value: str
    expires_at: float | None


class InMemoryCacheStore:
    """Process-local TTL cache implementing CacheStorePort."""

    def __init__(self) -> None:
        self._data: dict[str, _Entry] = {}

    def _purge_expired(self) -> None:
        now = time.monotonic()
        expired = [k for k, e in self._data.items() if e.expires_at is not None and e.expires_at <= now]
        for key in expired:
            del self._data[key]

    async def get(self, key: str) -> str | None:
        self._purge_expired()
        entry = self._data.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and entry.expires_at <= time.monotonic():
            del self._data[key]
            return None
        return entry.value

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds > 0 else None
        self._data[key] = _Entry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def delete_prefix(self, prefix: str) -> int:
        self._purge_expired()
        keys = [k for k in self._data if k.startswith(prefix)]
        for key in keys:
            del self._data[key]
        return len(keys)

    async def stats(self) -> dict[str, Any]:
        self._purge_expired()
        return {"keys": len(self._data), "backend": "memory"}
