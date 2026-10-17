"""Data intelligence DTOs — wire shapes for the intelligence report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ScoreComponentDTO:
    name: str
    score: float
    weight: float
    explanation: str


@dataclass(frozen=True, slots=True)
class DataQualityDTO:
    overall_score: float
    completeness: float
    consistency: float
    uniqueness: float
    validity: float
    integrity: float
    duplicate_percentage: float
    constant_columns: tuple[str, ...]
    near_constant_columns: tuple[str, ...]
    high_cardinality_columns: tuple[str, ...]
    low_cardinality_columns: tuple[str, ...]
    mixed_type_columns: tuple[str, ...]
    components: tuple[ScoreComponentDTO, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ColumnIntelligenceDTO:
    name: str
    detected_type: str
    semantic_type: str
    suggested_role: str
    identifier_probability: float
    target_probability: float
    null_percentage: float
    distinct_count: int
    entropy: float
    memory_bytes: int
    top_values: tuple[dict[str, Any], ...]
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    mode: str | None
    variance: float | None
    std_dev: float | None
    skewness: float | None
    kurtosis: float | None
    quantiles: dict[str, float] | None
    type_confidence: float
    potential_issues: tuple[str, ...]
    business_interpretation: str
    usability_score: float


@dataclass(frozen=True, slots=True)
class DistributionDTO:
    column: str
    histogram: dict[str, Any]
    box_plot: dict[str, Any]
    shape: str
    skewness: float | None
    kurtosis: float | None
    normality_indicator: str
    suggested_transformations: tuple[str, ...]
    interpretation: str


@dataclass(frozen=True, slots=True)
class MissingDataDTO:
    overall_missing_percentage: float
    columns_completely_missing: tuple[str, ...]
    column_missingness: tuple[dict[str, Any], ...]
    row_missingness_distribution: dict[str, Any]
    missingness_correlations: tuple[dict[str, Any], ...]
    heatmap: dict[str, Any]
    imputation_hints: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OutlierColumnDTO:
    column: str
    method: str
    outlier_count: int
    outlier_percentage: float
    extreme_values: tuple[float, ...]
    lower_bound: float | None
    upper_bound: float | None


@dataclass(frozen=True, slots=True)
class OutlierAnalysisDTO:
    columns: tuple[OutlierColumnDTO, ...]
    summary: str


@dataclass(frozen=True, slots=True)
class CorrelationPairDTO:
    column_a: str
    column_b: str
    pearson: float | None
    spearman: float | None
    kendall: float | None
    strength: str
    direction: str


@dataclass(frozen=True, slots=True)
class CorrelationAnalysisDTO:
    matrix: dict[str, Any]
    heatmap: dict[str, Any]
    strong_positive: tuple[CorrelationPairDTO, ...]
    strong_negative: tuple[CorrelationPairDTO, ...]
    weak_relationships: tuple[CorrelationPairDTO, ...]
    multicollinearity_warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FeatureRelationshipDTO:
    relationship_type: str
    column_a: str
    column_b: str
    strength: float
    pattern: str
    investigation_note: str


@dataclass(frozen=True, slots=True)
class DuplicateAnalysisDTO:
    duplicate_row_count: int
    duplicate_percentage: float
    duplicate_column_groups: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class DataHealthScoreDTO:
    overall_score: float
    category_scores: dict[str, float]
    explanation: str
    improvement_suggestions: tuple[str, ...]
    components: tuple[ScoreComponentDTO, ...]


@dataclass(frozen=True, slots=True)
class ReadinessItemDTO:
    category: str
    suitable: bool
    confidence: float
    explanation: str
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnalyticalReadinessDTO:
    items: tuple[ReadinessItemDTO, ...]
    overall_readiness: str
    requires_cleaning: bool
    requires_feature_engineering: bool
    requires_manual_review: bool


@dataclass(frozen=True, slots=True)
class IntelligenceOverviewDTO:
    dataset_id: UUID
    version_id: UUID
    version_number: int
    row_count: int
    column_count: int
    rows_sampled: int
    quality_score: float
    health_score: float
    trust_level: str
    headline_findings: tuple[str, ...]
    computed_at: datetime | None


@dataclass(frozen=True, slots=True)
class IntelligenceReportDTO:
    overview: IntelligenceOverviewDTO
    data_quality: DataQualityDTO
    schema_summary: tuple[dict[str, Any], ...]
    columns: tuple[ColumnIntelligenceDTO, ...]
    distributions: tuple[DistributionDTO, ...]
    missing_data: MissingDataDTO
    outliers: OutlierAnalysisDTO
    correlations: CorrelationAnalysisDTO
    feature_relationships: tuple[FeatureRelationshipDTO, ...]
    duplicates: DuplicateAnalysisDTO
    data_health: DataHealthScoreDTO
    analytical_readiness: AnalyticalReadinessDTO
    recommendations: tuple[str, ...]
