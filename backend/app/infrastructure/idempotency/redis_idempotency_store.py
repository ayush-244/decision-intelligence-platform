"""Redis-backed idempotency store."""

from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

_PREFIX = "delphi:idempotency"


class RedisIdempotencyStore:
    def __init__(self, client: Redis) -> None:
        self._client = client

    def _key(self, *, key: str, organization_id: str) -> str:
        return f"{_PREFIX}:{organization_id}:{key}"

    async def get_response(self, *, key: str, organization_id: str) -> dict[str, Any] | None:
        raw = await self._client.get(self._key(key=key, organization_id=organization_id))
        if raw is None:
            return None
        return json.loads(raw)

    async def store_response(
        self,
        *,
        key: str,
        organization_id: str,
        status_code: int,
        body: dict[str, Any],
        ttl_seconds: int,
    ) -> None:
        payload = json.dumps({"status_code": status_code, "body": body})
        await self._client.set(
            self._key(key=key, organization_id=organization_id),
            payload,
            ex=ttl_seconds,
        )

    async def claim_key(self, *, key: str, organization_id: str, ttl_seconds: int) -> bool:
        redis_key = self._key(key=key, organization_id=organization_id)
        return bool(
            await self._client.set(redis_key, json.dumps({"in_flight": True}), ex=ttl_seconds, nx=True)
        )
