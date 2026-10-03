"""AI Decision Copilot value objects."""

from __future__ import annotations

from enum import StrEnum


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class LlmProviderType(StrEnum):
    MOCK = "mock"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    GEMINI = "gemini"


class CopilotToolName(StrEnum):
    GET_STATISTICAL_ANALYSIS = "get_statistical_analysis"
    GET_CAUSAL_ANALYSIS = "get_causal_analysis"
    GET_SIMULATION = "get_simulation"
    GET_DECISION = "get_decision"
    GET_EXECUTIVE_REPORT = "get_executive_report"
    GET_DATA_QUALITY = "get_data_quality"
    GET_DECISION_SESSION = "get_decision_session"
    LIST_RECOMMENDATIONS = "list_recommendations"


class CitationResourceType(StrEnum):
    STATISTICAL_ANALYSIS = "statistical_analysis"
    CAUSAL_ANALYSIS = "causal_analysis"
    SIMULATION = "simulation"
    DECISION = "decision"
    EXECUTIVE_REPORT = "executive_report"
    INTELLIGENCE_REPORT = "intelligence_report"
    DECISION_SESSION = "decision_session"
    RECOMMENDATION = "recommendation"


PROMPT_TEMPLATE_VERSION = "1.0.0"

SUGGESTED_QUESTIONS: tuple[str, ...] = (
    "Explain why Delphi recommends this intervention.",
    "What assumptions affect this recommendation?",
    "Summarize the findings for the CEO.",
    "Compare the top two scenarios.",
    "What evidence supports the primary recommendation?",
)
