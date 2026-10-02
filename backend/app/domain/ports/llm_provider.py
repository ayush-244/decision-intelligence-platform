"""LLM provider port — vendor-agnostic completion interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LlmMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class LlmCompletionRequest:
    messages: list[LlmMessage]
    system_prompt: str
    max_tokens: int = 2048
    temperature: float = 0.2
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LlmCompletionResponse:
    content: str
    provider: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


class LlmProviderPort(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse: ...
