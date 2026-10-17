"""OpenAI-compatible LLM provider using httpx."""

from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.logging import get_logger
from app.domain.ports.llm_provider import (
    LlmCompletionRequest,
    LlmCompletionResponse,
    LlmProviderPort,
)

_logger = get_logger(__name__)


class OpenAiLlmProvider(LlmProviderPort):
    """Calls OpenAI Chat Completions API — swappable for Azure via base_url."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "openai"

    async def complete(self, request: LlmCompletionRequest) -> LlmCompletionResponse:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": request.system_prompt},
            *[{"role": m.role, "content": m.content} for m in request.messages],
        ]
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        _logger.info(
            "llm_completion",
            provider=self.provider_name,
            model=self._model,
            tokens=usage.get("total_tokens"),
        )
        return LlmCompletionResponse(
            content=content,
            provider=self.provider_name,
            model=self._model,
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
        )
