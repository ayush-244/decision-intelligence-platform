"""Queue facade with depth introspection."""

from __future__ import annotations

from uuid import UUID

from app.domain.ports.job_queue import JobQueuePort


class QueueManager:
    """Thin wrapper over JobQueuePort for monitoring and orchestration."""

    def __init__(self, queue: JobQueuePort) -> None:
        self._queue = queue

    async def depth(self) -> int:
        return await self._queue.queue_depth()

    async def enqueue(self, *, job_id: UUID, priority: int = 0) -> None:
        await self._queue.enqueue(job_id=job_id, priority=priority)

    async def remove(self, *, job_id: UUID) -> None:
        await self._queue.remove(job_id=job_id)
