"""Job queue port — enqueue and dequeue background work."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class JobQueuePort(ABC):
    @abstractmethod
    async def enqueue(self, *, job_id: UUID, priority: int = 0) -> None: ...

    @abstractmethod
    async def dequeue(self, *, timeout_seconds: float = 1.0) -> UUID | None: ...

    @abstractmethod
    async def queue_depth(self) -> int: ...

    @abstractmethod
    async def remove(self, *, job_id: UUID) -> None: ...
