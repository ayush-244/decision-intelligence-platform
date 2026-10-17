"""LLM provider factory — selects vendor from configuration."""

from __future__ import annotations

from app.core.config import Settings
from app.domain.ports.llm_provider import LlmProviderPort
from app.domain.value_objects.copilot import LlmProviderType
from app.infrastructure.llm.mock_llm_provider import MockLlmProvider
from app.infrastructure.llm.openai_llm_provider import OpenAiLlmProvider


def create_llm_provider(settings: Settings) -> LlmProviderPort:
    provider = settings.llm_provider.lower()
    if provider == LlmProviderType.OPENAI.value and settings.openai_api_key:
        return OpenAiLlmProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
        )
    return MockLlmProvider()
