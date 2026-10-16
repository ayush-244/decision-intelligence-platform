"""In-memory dead-letter queue."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from app.shared.utils.datetime import utc_now


@dataclass(frozen=True, slots=True)
class DeadLetterEntry:
    id: UUID
    source: str
    payload: dict[str, Any]
    error_message: str
    organization_id: UUID | None
    created_at: str


class InMemoryDeadLetterQueue:
    def __init__(self) -> None:
        self._entries: list[DeadLetterEntry] = field(default_factory=list)
        self._entries = []

    async def push(
        self,
        *,
        source: str,
        payload: dict[str, Any],
        error_message: str,
        organization_id: UUID | None = None,
    ) -> None:
        self._entries.append(
            DeadLetterEntry(
                id=uuid4(),
                source=source,
                payload=payload,
                error_message=error_message,
                organization_id=organization_id,
                created_at=utc_now().isoformat(),
            )
        )

    async def depth(self) -> int:
        return len(self._entries)
