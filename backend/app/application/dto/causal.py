"""Causal inference DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.value_objects.causal import CausalEstimatorType, IdentificationStrategy


@dataclass(frozen=True, slots=True)
class CausalVariableRoleDTO:
    name: str
    role: str
    confidence: float
    reasoning: str


@dataclass(frozen=True, slots=True)
class DAGNodeDTO:
    id: str
    label: str
    role: str | None = None
    position: dict[str, float] | None = None


@dataclass(frozen=True, slots=True)
class DAGEdgeDTO:
    source: str
    target: str


@dataclass(frozen=True, slots=True)
class DAGDTO:
    nodes: tuple[DAGNodeDTO, ...]
    edges: tuple[DAGEdgeDTO, ...]
    is_valid: bool
    validation_errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AssumptionCheckDTO:
    name: str
    status: str
    explanation: str
    recommendation: str | None = None


@dataclass(frozen=True, slots=True)
class AssumptionReportDTO:
    checks: tuple[AssumptionCheckDTO, ...]
    all_passed: bool
    required_assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IdentificationReportDTO:
    strategy: IdentificationStrategy
    identified: bool
    adjustment_set: tuple[str, ...]
    reasoning: str
    required_assumptions: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TreatmentEffectDTO:
    estimator: CausalEstimatorType
    ate: float | None
    att: float | None
    atc: float | None
    std_error: float | None
    confidence_level: float
    ci_lower: float | None
    ci_upper: float | None
    p_value: float | None
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RefutationResultDTO:
    method: str
    original_effect: float
    refuted_effect: float
    passed: bool
    explanation: str


@dataclass(frozen=True, slots=True)
class SensitivityResultDTO:
    robustness_score: float
    gamma_threshold: float | None
    explanation: str
    violations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CausalInterpretationDTO:
    objective: str
    business_interpretation: str
    limitations: tuple[str, ...]
    recommended_next_steps: tuple[str, ...]
    causal_claim_valid: bool


@dataclass(frozen=True, slots=True)
class CausalAnalysisRequestDTO:
    dataset_id: str
    version_id: str | None
    dag_id: str | None
    treatment: str
    outcome: str
    business_question: str
    estimator: CausalEstimatorType | None
    confidence_level: float
    adjustment_set: tuple[str, ...] | None
    run_refutation: bool
    run_sensitivity: bool


@dataclass(frozen=True, slots=True)
class CausalAnalysisResultDTO:
    variable_roles: tuple[CausalVariableRoleDTO, ...]
    dag: DAGDTO
    assumption_report: AssumptionReportDTO
    identification: IdentificationReportDTO
    treatment_effect: TreatmentEffectDTO
    refutation_results: tuple[RefutationResultDTO, ...]
    sensitivity: SensitivityResultDTO | None
    interpretation: CausalInterpretationDTO
