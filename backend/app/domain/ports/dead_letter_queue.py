"""Dead-letter queue port — failed jobs/messages for manual replay."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class DeadLetterQueuePort(ABC):
    @abstractmethod
    async def push(
        self,
        *,
        source: str,
        payload: dict[str, Any],
        error_message: str,
        organization_id: UUID | None = None,
    ) -> None: ...

    @abstractmethod
    async def depth(self) -> int: ...
