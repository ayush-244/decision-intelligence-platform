"""Explainable scoring for data health and analytical readiness."""

from __future__ import annotations

from app.application.dto.intelligence import (
    AnalyticalReadinessDTO,
    ColumnIntelligenceDTO,
    DataHealthScoreDTO,
    DataQualityDTO,
    MissingDataDTO,
    OutlierAnalysisDTO,
    ReadinessItemDTO,
    ScoreComponentDTO,
)
from app.core.config import Settings


def compute_health_score(
    *,
    quality: DataQualityDTO,
    missing: MissingDataDTO,
    outliers: OutlierAnalysisDTO,
    columns: tuple[ColumnIntelligenceDTO, ...],
    settings: Settings,
) -> DataHealthScoreDTO:
    weights = settings.health_score_weights

    missing_penalty = min(100.0, missing.overall_missing_percentage * 1.5)
    missing_score = max(0.0, 100.0 - missing_penalty)

    outlier_pct = (
        sum(col.outlier_percentage for col in outliers.columns) / len(outliers.columns)
        if outliers.columns
        else 0.0
    )
    outlier_score = max(0.0, 100.0 - min(100.0, outlier_pct * 2))

    usability_avg = (
        sum(col.usability_score for col in columns) / len(columns) if columns else 0.0
    )

    distribution_score = max(
        0.0,
        100.0 - len(quality.constant_columns) * 10 - len(quality.near_constant_columns) * 3,
    )

    cardinality_score = max(
        0.0,
        100.0 - len(quality.high_cardinality_columns) * 5,
    )

    category_scores = {
        "data_quality": quality.overall_score,
        "missingness": round(missing_score, 1),
        "outliers": round(outlier_score, 1),
        "column_usability": round(usability_avg, 1),
        "distributions": round(distribution_score, 1),
        "cardinality": round(cardinality_score, 1),
    }

    overall = (
        quality.overall_score * weights["data_quality"]
        + missing_score * weights["missingness"]
        + outlier_score * weights["outliers"]
        + usability_avg * weights["column_usability"]
        + distribution_score * weights["distributions"]
        + cardinality_score * weights["cardinality"]
    )

    components = (
        ScoreComponentDTO(
            "data_quality",
            quality.overall_score,
            weights["data_quality"],
            "Weighted completeness, uniqueness, consistency, validity, integrity.",
        ),
        ScoreComponentDTO(
            "missingness",
            round(missing_score, 1),
            weights["missingness"],
            f"Overall missing rate: {missing.overall_missing_percentage:.1f}%.",
        ),
        ScoreComponentDTO(
            "outliers",
            round(outlier_score, 1),
            weights["outliers"],
            f"Average outlier burden across numeric columns: {outlier_pct:.1f}%.",
        ),
        ScoreComponentDTO(
            "column_usability",
            round(usability_avg, 1),
            weights["column_usability"],
            "Average per-column usability after null/identifier penalties.",
        ),
        ScoreComponentDTO(
            "distributions",
            round(distribution_score, 1),
            weights["distributions"],
            "Penalizes constant and near-constant features.",
        ),
        ScoreComponentDTO(
            "cardinality",
            round(cardinality_score, 1),
            weights["cardinality"],
            "Penalizes suspicious high-cardinality columns.",
        ),
    )

    suggestions: list[str] = []
    if missing.overall_missing_percentage > 15:
        suggestions.append("Address missing data before running inferential models.")
    if quality.duplicate_percentage > 5:
        suggestions.append("Investigate duplicate rows — deduplicate if unintended.")
    if outliers.columns:
        suggestions.append("Review outlier columns for data entry errors vs genuine extremes.")
    if quality.high_cardinality_columns:
        suggestions.append("Confirm identifier columns are excluded from feature sets.")
    if quality.constant_columns:
        suggestions.append("Drop constant columns — they carry no information.")

    explanation = (
        f"Health score {overall:.1f}/100 combines quality ({quality.overall_score:.0f}), "
        f"missingness ({missing_score:.0f}), outliers ({outlier_score:.0f}), and column usability."
    )

    return DataHealthScoreDTO(
        overall_score=round(overall, 1),
        category_scores=category_scores,
        explanation=explanation,
        improvement_suggestions=tuple(suggestions),
        components=components,
    )


def assess_analytical_readiness(
    *,
    quality: DataQualityDTO,
    missing: MissingDataDTO,
    columns: tuple[ColumnIntelligenceDTO, ...],
    health: DataHealthScoreDTO,
) -> AnalyticalReadinessDTO:
    numeric_features = [c for c in columns if c.semantic_type in {"integer", "float"}]
    categorical_features = [c for c in columns if c.semantic_type == "categorical"]
    target_candidates = [c for c in columns if c.target_probability >= 0.5]
    id_cols = [c for c in columns if c.identifier_probability >= 0.7]

    blockers_cleaning: list[str] = []
    if missing.overall_missing_percentage > 25:
        blockers_cleaning.append("High overall missingness")
    if quality.duplicate_percentage > 10:
        blockers_cleaning.append("Significant duplicate rows")
    if quality.constant_columns:
        blockers_cleaning.append("Constant columns present")

    items: list[ReadinessItemDTO] = [
        ReadinessItemDTO(
            category="regression",
            suitable=len(numeric_features) >= 2 and health.overall_score >= 60,
            confidence=min(0.95, health.overall_score / 100),
            explanation="Requires numeric features and moderate data health.",
            blockers=tuple(blockers_cleaning),
        ),
        ReadinessItemDTO(
            category="classification",
            suitable=len(categorical_features) + len(target_candidates) >= 1
            and health.overall_score >= 55,
            confidence=min(0.9, health.overall_score / 100),
            explanation="Needs a categorical target or label candidate plus usable features.",
            blockers=tuple(blockers_cleaning),
        ),
        ReadinessItemDTO(
            category="clustering",
            suitable=len(numeric_features) >= 2 and missing.overall_missing_percentage < 30,
            confidence=0.75 if len(numeric_features) >= 3 else 0.5,
            explanation="Unsupervised clustering works best with complete numeric features.",
            blockers=tuple(blockers_cleaning),
        ),
        ReadinessItemDTO(
            category="causal_inference",
            suitable=health.overall_score >= 70
            and len(id_cols) == 0
            and missing.overall_missing_percentage < 15,
            confidence=0.6,
            explanation=(
                "Causal analysis needs clean data, clear variables, and domain-specified DAGs — "
                "automated checks are conservative."
            ),
            blockers=tuple(
                blockers_cleaning
                + (["Identifier columns detected"] if id_cols else [])
                + ["Manual DAG specification required"]
            ),
        ),
    ]

    requires_cleaning = bool(blockers_cleaning)
    requires_fe = len(quality.high_cardinality_columns) > 0 or len(categorical_features) > 5
    requires_review = health.overall_score < 65 or bool(id_cols)

    if health.overall_score >= 80:
        overall = "high"
    elif health.overall_score >= 60:
        overall = "moderate"
    else:
        overall = "low"

    return AnalyticalReadinessDTO(
        items=tuple(items),
        overall_readiness=overall,
        requires_cleaning=requires_cleaning,
        requires_feature_engineering=requires_fe,
        requires_manual_review=requires_review,
    )


def build_recommendations(
    *,
    quality: DataQualityDTO,
    missing: MissingDataDTO,
    health: DataHealthScoreDTO,
    readiness: AnalyticalReadinessDTO,
) -> tuple[str, ...]:
    recs = list(health.improvement_suggestions)
    recs.extend(missing.imputation_hints)
    if readiness.requires_manual_review:
        recs.append("Schedule a manual data review before production analyses.")
    if quality.overall_score < 70:
        recs.append("Improve data quality at source — collection issues may persist across versions.")
    return tuple(dict.fromkeys(recs))
