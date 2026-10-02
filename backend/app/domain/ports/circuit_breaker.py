"""Circuit breaker port — prevents cascade failures against dependencies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class CircuitBreakerPort(ABC):
    @abstractmethod
    async def call(
        self,
        *,
        name: str,
        operation: Callable[[], Awaitable[T]],
    ) -> T: ...

    @abstractmethod
    def state(self, *, name: str) -> str: ...
