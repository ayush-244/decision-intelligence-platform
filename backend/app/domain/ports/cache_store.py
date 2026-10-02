"""Version-aware cache store port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CacheStorePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def delete_prefix(self, prefix: str) -> int: ...

    @abstractmethod
    async def stats(self) -> dict[str, Any]: ...
