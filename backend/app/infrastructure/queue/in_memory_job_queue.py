"""In-memory FIFO job queue for tests."""

from __future__ import annotations

import asyncio
from uuid import UUID


class InMemoryJobQueue:
    """Async-safe in-process queue implementing JobQueuePort."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[UUID] = asyncio.Queue()
        self._pending: set[UUID] = set()

    async def enqueue(self, *, job_id: UUID, priority: int = 0) -> None:
        del priority  # priority ordering reserved for Redis sorted-set backend
        if job_id in self._pending:
            return
        self._pending.add(job_id)
        await self._queue.put(job_id)

    async def dequeue(self, *, timeout_seconds: float = 1.0) -> UUID | None:
        try:
            job_id = await asyncio.wait_for(self._queue.get(), timeout=timeout_seconds)
        except TimeoutError:
            return None
        self._pending.discard(job_id)
        return job_id

    async def queue_depth(self) -> int:
        return self._queue.qsize()

    async def remove(self, *, job_id: UUID) -> None:
        self._pending.discard(job_id)
