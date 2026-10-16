"""Redis list-backed job queue."""

from __future__ import annotations

from uuid import UUID

from redis.asyncio import Redis

_QUEUE_KEY = "delphi:jobs:queue"
_REMOVED_SET = "delphi:jobs:removed"


class RedisJobQueue:
    """FIFO queue using Redis RPUSH / BLPOP."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def enqueue(self, *, job_id: UUID, priority: int = 0) -> None:
        del priority
        await self._client.srem(_REMOVED_SET, str(job_id))
        await self._client.rpush(_QUEUE_KEY, str(job_id))

    async def dequeue(self, *, timeout_seconds: float = 1.0) -> UUID | None:
        timeout = max(int(timeout_seconds), 1)
        result = await self._client.blpop(_QUEUE_KEY, timeout=timeout)
        if result is None:
            return None
        _, raw = result
        job_id = UUID(raw)
        if await self._client.sismember(_REMOVED_SET, raw):
            return None
        return job_id

    async def queue_depth(self) -> int:
        return int(await self._client.llen(_QUEUE_KEY))

    async def remove(self, *, job_id: UUID) -> None:
        await self._client.sadd(_REMOVED_SET, str(job_id))
        await self._client.lrem(_QUEUE_KEY, 0, str(job_id))
