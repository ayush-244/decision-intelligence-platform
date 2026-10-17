"""Decision intelligence DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ObjectiveWeightDTO:
    objective: str
    weight: float


@dataclass(frozen=True, slots=True)
class DecisionConstraintDTO:
    type: str
    severity: str
    threshold: float | None
    description: str


@dataclass(frozen=True, slots=True)
class EvidenceChainDTO:
    statistical_analysis_id: str | None
    causal_analysis_id: str
    simulation_run_id: str
    scenario_id: str
    statistical_summary: str | None
    causal_summary: str
    simulation_summary: str


@dataclass(frozen=True, slots=True)
class DecisionScoreDTO:
    business_impact: float
    roi: float
    confidence: float
    risk: float
    feasibility: float
    strategic_alignment: float
    constraint_satisfaction: float
    overall_score: float
    methodology: str


@dataclass(frozen=True, slots=True)
class TradeoffDTO:
    dimension_a: str
    dimension_b: str
    option_a: str
    option_b: str
    tradeoff_summary: str
    recommendation: str


@dataclass(frozen=True, slots=True)
class PriorityDTO:
    simulation_run_id: str
    title: str
    priority_score: float
    rank: int
    factors: tuple[tuple[str, float, str], ...]


@dataclass(frozen=True, slots=True)
class RecommendationDTO:
    rank: int
    status: str
    title: str
    summary: str
    reason: str
    evidence: EvidenceChainDTO
    expected_outcome: float
    confidence: float
    roi: float
    risk: float
    required_assumptions: tuple[str, ...]
    implementation_difficulty: str
    expected_timeline: str
    dependencies: tuple[str, ...]
    alternative_options: tuple[str, ...]
    business_explanation: str
    recommended_order: int
    decision_score: DecisionScoreDTO
    validation_passed: bool
    validation_notes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DecisionRequestDTO:
    dataset_id: str
    version_id: str | None
    name: str
    primary_objective: str
    simulation_run_ids: tuple[str, ...]
    objective_weights: tuple[ObjectiveWeightDTO, ...]
    constraints: tuple[DecisionConstraintDTO, ...]
    risk_tolerance: float
    min_confidence: float
    max_budget: float | None


@dataclass(frozen=True, slots=True)
class DecisionResultDTO:
    recommendations: tuple[RecommendationDTO, ...]
    rejected: tuple[RecommendationDTO, ...]
    tradeoffs: tuple[TradeoffDTO, ...]
    priorities: tuple[PriorityDTO, ...]
    objectives_analyzed: tuple[str, ...]
    constraint_evaluations: tuple[dict[str, Any], ...]
    overall_summary: str
    recommended_first: str | None
    deferred: tuple[str, ...]
    assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
