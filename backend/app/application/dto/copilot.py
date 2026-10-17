"""AI Copilot DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CitationDTO:
    resource_type: str
    resource_id: str
    label: str
    excerpt: str


@dataclass(frozen=True, slots=True)
class CopilotMessageDTO:
    id: str
    role: str
    content: str
    citations: list[CitationDTO]
    created_at: str


@dataclass(frozen=True, slots=True)
class CopilotConversationDTO:
    id: str
    title: str
    dataset_id: str | None
    session_id: str | None
    messages: list[CopilotMessageDTO]
    pinned_insights: list[str]
    suggested_questions: list[str]
    context_summary: dict[str, Any]
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SendMessageRequestDTO:
    content: str
    dataset_id: str | None = None
    session_id: str | None = None


@dataclass(frozen=True, slots=True)
class CreateConversationRequestDTO:
    title: str
    dataset_id: str | None = None
    session_id: str | None = None


@dataclass(frozen=True, slots=True)
class StructuredContext:
    """Verified analytical context — never includes raw unverified data."""

    dataset: dict[str, Any] = field(default_factory=dict)
    data_quality: dict[str, Any] = field(default_factory=dict)
    statistics: list[dict[str, Any]] = field(default_factory=list)
    causal: list[dict[str, Any]] = field(default_factory=list)
    simulations: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    reports: list[dict[str, Any]] = field(default_factory=list)
    session: dict[str, Any] | None = None
    evidence_index: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_prompt_sections(self) -> str:
        """Render structured context for the LLM — concise, not raw JSON dump."""
        lines: list[str] = []
        if self.dataset:
            lines.append(f"Dataset: {self.dataset.get('name', 'unknown')} (id={self.dataset.get('id')})")
        if self.data_quality:
            lines.append(
                f"Data quality score: {self.data_quality.get('health_score')} "
                f"({self.data_quality.get('quality_score')} completeness-related)"
            )
        for stat in self.statistics[:5]:
            lines.append(
                f"[Statistical Analysis #{stat.get('short_id')}] {stat.get('goal')}: "
                f"{stat.get('summary', 'completed')}"
            )
        for c in self.causal[:3]:
            lines.append(
                f"[Causal Analysis #{c.get('short_id')}] treatment={c.get('treatment')} "
                f"outcome={c.get('outcome')}: {c.get('summary', '')}"
            )
        for s in self.simulations[:3]:
            lines.append(
                f"[Simulation #{s.get('short_id')}] {s.get('name')}: {s.get('summary', '')}"
            )
        for d in self.decisions[:3]:
            lines.append(
                f"[Decision #{d.get('short_id')}] objective={d.get('objective')}: "
                f"top recommendation={d.get('top_recommendation', 'n/a')}"
            )
        for r in self.reports[:2]:
            lines.append(f"[Executive Report #{r.get('short_id')}] {r.get('name')}: {r.get('summary', '')}")
        if self.session:
            lines.append(f"Decision session: {self.session.get('name')} at step {self.session.get('current_step')}")
        return "\n".join(lines) if lines else "No verified analytical outputs available yet."
