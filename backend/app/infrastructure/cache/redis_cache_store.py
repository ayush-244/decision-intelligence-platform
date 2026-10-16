"""Redis-backed cache store with prefix invalidation."""

from __future__ import annotations

from typing import Any

from redis.asyncio import Redis


class RedisCacheStore:
    """Version-aware cache backend using Redis string keys with TTL."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        await self._client.set(key, value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def delete_prefix(self, prefix: str) -> int:
        deleted = 0
        async for key in self._client.scan_iter(match=f"{prefix}*"):
            await self._client.delete(key)
            deleted += 1
        return deleted

    async def stats(self) -> dict[str, Any]:
        info = await self._client.info("keyspace")
        db_key = next((k for k in info if k.startswith("db")), None)
        keys = 0
        if db_key:
            keys = int(str(info[db_key]).split("keys=")[-1].split(",")[0])
        return {"keys": keys, "backend": "redis"}
