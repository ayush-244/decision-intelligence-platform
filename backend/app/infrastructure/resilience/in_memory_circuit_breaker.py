"""In-process circuit breaker with open/half-open/closed states."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TypeVar

from app.shared.exceptions import ServiceUnavailableError

T = TypeVar("T")


@dataclass
class _BreakerState:
    failures: int = 0
    opened_at: float | None = None
    state: str = "closed"


class InMemoryCircuitBreaker:
    """Simple circuit breaker — suitable for monolith and tests."""

    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_seconds
        self._breakers: dict[str, _BreakerState] = field(default_factory=dict)
        self._breakers = {}

    def state(self, *, name: str) -> str:
        return self._resolve(name).state

    async def call(
        self,
        *,
        name: str,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        breaker = self._resolve(name)
        now = time.monotonic()

        if breaker.state == "open":
            if breaker.opened_at and now - breaker.opened_at >= self._recovery_timeout:
                breaker.state = "half_open"
            else:
                raise ServiceUnavailableError(
                    f"Circuit '{name}' is open.",
                    code="circuit_open",
                )

        try:
            result = await operation()
        except Exception:
            breaker.failures += 1
            if breaker.failures >= self._failure_threshold:
                breaker.state = "open"
                breaker.opened_at = now
            raise

        breaker.failures = 0
        breaker.state = "closed"
        breaker.opened_at = None
        return result

    def _resolve(self, name: str) -> _BreakerState:
        if name not in self._breakers:
            self._breakers[name] = _BreakerState()
        return self._breakers[name]
