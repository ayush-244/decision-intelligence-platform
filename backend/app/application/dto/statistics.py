"""Statistical analysis DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.value_objects.statistics import StatisticalTestType


@dataclass(frozen=True, slots=True)
class VariableSpecDTO:
    name: str
    role: str


@dataclass(frozen=True, slots=True)
class AnalysisRequestDTO:
    dataset_id: UUID
    version_id: UUID | None
    goal: str
    research_question: str
    variables: tuple[VariableSpecDTO, ...]
  # Optional override — if None, engine selects test
    test_type: StatisticalTestType | None = None
    confidence_level: float = 0.95
    reference_value: float | None = None


@dataclass(frozen=True, slots=True)
class AssumptionCheckDTO:
    name: str
    status: str
    statistic: float | None
    p_value: float | None
    explanation: str
    recommendation: str | None = None


@dataclass(frozen=True, slots=True)
class AssumptionReportDTO:
    checks: tuple[AssumptionCheckDTO, ...]
    all_passed: bool
    alternatives: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EffectSizeDTO:
    name: str
    value: float
    interpretation: str
    magnitude: str


@dataclass(frozen=True, slots=True)
class ConfidenceIntervalDTO:
    parameter: str
    lower: float
    upper: float
    level: float
    interpretation: str


@dataclass(frozen=True, slots=True)
class TestRecommendationDTO:
    recommended_test: StatisticalTestType
    confidence: float
    reasoning: str
    expected_assumptions: tuple[str, ...]
    limitations: tuple[str, ...]
    alternatives: tuple[StatisticalTestType, ...]


@dataclass(frozen=True, slots=True)
class StatisticalTestResultDTO:
    test_type: StatisticalTestType
    statistic: float | None
    p_value: float | None
    degrees_of_freedom: float | None
    is_significant: bool
    alpha: float
    details: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RegressionDiagnosticsDTO:
    r_squared: float | None
    adj_r_squared: float | None
    coefficients: tuple[dict[str, Any], ...]
    vif: tuple[dict[str, Any], ...]
    residual_summary: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AnalysisInterpretationDTO:
    test_performed: str
    selection_reason: str
    practical_significance: str
    business_interpretation: str
    limitations: tuple[str, ...]
    recommended_next_steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnalysisResultDTO:
    assumption_report: AssumptionReportDTO
    test_result: StatisticalTestResultDTO | None
    effect_sizes: tuple[EffectSizeDTO, ...]
    confidence_intervals: tuple[ConfidenceIntervalDTO, ...]
    regression: RegressionDiagnosticsDTO | None
    interpretation: AnalysisInterpretationDTO
    descriptive: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AnalysisRunDTO:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    status: str
    goal: str
    test_type: str | None
    research_question: str
    result: AnalysisResultDTO | None
    error_message: str | None
    executed_at: datetime | None
    created_at: datetime
