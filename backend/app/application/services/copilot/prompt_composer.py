"""Versioned prompt templates — no business logic in strings."""

from __future__ import annotations

from app.application.dto.copilot import StructuredContext
from app.domain.value_objects.copilot import PROMPT_TEMPLATE_VERSION


class CopilotPromptComposer:
    """Compose system and user prompts from verified context."""

    SYSTEM_PROMPT = """You are Delphi's AI Decision Copilot — a senior business analyst.

RULES (non-negotiable):
1. NEVER invent numbers, treatment effects, p-values, or recommendations.
2. ONLY reference analyses present in the VERIFIED CONTEXT below.
3. NEVER perform statistical or causal calculations — Delphi engines already did.
4. Cite evidence using labels like [Statistical Analysis #1], [Decision #2].
5. If evidence is insufficient, say so clearly.
6. Translate technical findings into executive business language.
7. Distinguish assumptions from conclusions.

Prompt template version: {version}
"""

    def compose_system(self, context: StructuredContext) -> str:
        base = self.SYSTEM_PROMPT.format(version=PROMPT_TEMPLATE_VERSION)
        sections = context.to_prompt_sections()
        return f"{base}\n\nVERIFIED CONTEXT:\n{sections}"

    def compose_user(self, *, user_message: str, conversation_history: str = "") -> str:
        if conversation_history:
            return f"Prior conversation:\n{conversation_history}\n\nUser question: {user_message}"
        return user_message

    @property
    def prompt_version(self) -> str:
        return PROMPT_TEMPLATE_VERSION
