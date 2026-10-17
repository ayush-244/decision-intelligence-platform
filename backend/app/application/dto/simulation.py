"""Simulation engine DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class InterventionDTO:
    variable: str
    mode: str
    value: float | str | bool
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ConstraintDTO:
    type: str
    severity: str
    threshold: float | None
    description: str
    value: float | None = None


@dataclass(frozen=True, slots=True)
class InterventionValidationDTO:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CounterfactualOutcomeDTO:
    baseline_outcome: float
    expected_outcome: float
    expected_treatment_effect: float
    ci_lower: float
    ci_upper: float
    probability_improvement: float
    probability_deterioration: float
    uncertainty_score: float
    extrapolation_warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MonteCarloResultDTO:
    iterations: int
    expected_value: float
    median: float
    p05: float
    p25: float
    p75: float
    p95: float
    tail_risk: float
    distribution: tuple[float, ...]
    methodology: str


@dataclass(frozen=True, slots=True)
class ConstraintEvaluationDTO:
    constraint: ConstraintDTO
    satisfied: bool
    actual_value: float | None
    message: str


@dataclass(frozen=True, slots=True)
class RiskContributorDTO:
    name: str
    score: float
    weight: float
    explanation: str


@dataclass(frozen=True, slots=True)
class RiskAssessmentDTO:
    overall_score: float
    implementation_risk: float
    statistical_uncertainty: float
    sensitivity_risk: float
    model_confidence: float
    hidden_confounding_risk: float
    operational_risk: float
    contributors: tuple[RiskContributorDTO, ...]
    summary: str


@dataclass(frozen=True, slots=True)
class ROIEstimateDTO:
    expected_cost: float
    expected_revenue: float
    expected_savings: float
    expected_roi: float
    payback_period: float | None
    cost_benefit_ratio: float
    assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ScenarioComparisonDTO:
    scenario_id: str
    scenario_name: str
    expected_outcome: float
    expected_roi: float | None
    risk_score: float
    rank: int


@dataclass(frozen=True, slots=True)
class SimulationInterpretationDTO:
    scenario_summary: str
    business_interpretation: str
    limitations: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    alternative_scenarios: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SimulationRequestDTO:
    dataset_id: str
    version_id: str | None
    causal_analysis_id: str
    statistical_analysis_id: str | None
    scenario_id: str | None
    name: str
    objective: str
    interventions: tuple[InterventionDTO, ...]
    constraints: tuple[ConstraintDTO, ...]
    comparison_scenario_ids: tuple[str, ...]
    monte_carlo_iterations: int
    confidence_level: float
    roi_assumptions: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SimulationResultDTO:
    counterfactual: CounterfactualOutcomeDTO
    monte_carlo: MonteCarloResultDTO
    constraint_evaluations: tuple[ConstraintEvaluationDTO, ...]
    risk: RiskAssessmentDTO
    roi: ROIEstimateDTO
    comparison: tuple[ScenarioComparisonDTO, ...]
    interpretation: SimulationInterpretationDTO
    assumptions: tuple[str, ...]
