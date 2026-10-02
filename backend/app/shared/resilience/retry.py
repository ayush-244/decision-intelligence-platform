"""Retry policy with exponential backoff."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.logging import get_logger

_logger = get_logger(__name__)
T = TypeVar("T")


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.5,
    operation_name: str = "operation",
) -> T:
    """Execute an async operation with bounded retries and exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= max_attempts:
                break
            delay = base_delay_seconds * (2 ** (attempt - 1))
            _logger.warning(
                "retry_attempt",
                operation=operation_name,
                attempt=attempt,
                delay_seconds=delay,
                error=str(exc),
            )
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error
