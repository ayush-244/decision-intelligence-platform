"""Executive intelligence DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceChainNarrativeDTO:
    statistical: str | None
    causal: str
    simulation: str
    decision: str
    confidence_level: str
    confidence_score: float


@dataclass(frozen=True, slots=True)
class ExplainabilityBlockDTO:
    recommendation_title: str
    why: str
    evidence: EvidenceChainNarrativeDTO
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    business_interpretation: str
    alternative_actions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TimelineItemDTO:
    priority: int
    title: str
    effort: str
    impact: str
    dependencies: tuple[str, ...]
    milestones: tuple[str, ...]
    timeline: str
    business_owner: str
    risk_level: str
    expected_kpi_changes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExecutiveReportDTO:
    executive_summary: str
    business_objective: str
    key_findings: tuple[str, ...]
    decision_summary: str
    top_recommendations: tuple[dict[str, Any], ...]
    expected_roi: dict[str, Any]
    expected_risks: dict[str, Any]
    confidence_assessment: dict[str, Any]
    key_assumptions: tuple[str, ...]
    tradeoffs: tuple[dict[str, Any], ...]
    scenario_comparison: tuple[dict[str, Any], ...]
    implementation_roadmap: tuple[TimelineItemDTO, ...]
    business_kpis: tuple[dict[str, Any], ...]
    explainability: tuple[ExplainabilityBlockDTO, ...]
    appendix: dict[str, Any]
    narrative: str


@dataclass(frozen=True, slots=True)
class GenerateReportRequestDTO:
    dataset_id: str
    version_id: str | None
    decision_run_id: str | None
    name: str
    business_objective: str
    include_technical_appendix: bool


@dataclass(frozen=True, slots=True)
class DashboardSnapshotDTO:
    business_health_score: float
    decision_pipeline: dict[str, int]
    recommendation_status: dict[str, int]
    roi_overview: dict[str, float]
    risk_overview: dict[str, float]
    confidence_overview: dict[str, float]
    recent_decisions: tuple[dict[str, Any], ...]
    historical_reports: int
