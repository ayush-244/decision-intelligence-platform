"""Statistical analyzers for the data intelligence engine.

Each function is pure over a Polars DataFrame and independently testable.
"""

from __future__ import annotations

import math
from typing import Any

import polars as pl

from app.application.dto.intelligence import (
    ColumnIntelligenceDTO,
    CorrelationAnalysisDTO,
    CorrelationPairDTO,
    DataQualityDTO,
    DistributionDTO,
    DuplicateAnalysisDTO,
    FeatureRelationshipDTO,
    MissingDataDTO,
    OutlierAnalysisDTO,
    OutlierColumnDTO,
    ScoreComponentDTO,
)
from app.core.config import Settings

_NUMERIC_DTYPES = {
    pl.Int8,
    pl.Int16,
    pl.Int32,
    pl.Int64,
    pl.UInt8,
    pl.UInt16,
    pl.UInt32,
    pl.UInt64,
    pl.Float32,
    pl.Float64,
}


def _is_numeric(dtype: pl.DataType) -> bool:
    return dtype in _NUMERIC_DTYPES


def _entropy_from_counts(counts: list[int], total: int) -> float:
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts:
        if count <= 0:
            continue
        p = count / total
        entropy -= p * math.log2(p)
    return round(entropy, 4)


def _histogram_bins(series: pl.Series, bins: int = 20) -> dict[str, Any]:
    non_null = series.drop_nulls().cast(pl.Float64, strict=False)
    if non_null.len() == 0:
        return {"bins": [], "counts": []}
    min_val = float(non_null.min())  # type: ignore[arg-type]
    max_val = float(non_null.max())  # type: ignore[arg-type]
    if min_val == max_val:
        return {"bins": [min_val, max_val], "counts": [non_null.len()]}
    step = (max_val - min_val) / bins
    edges = [min_val + step * i for i in range(bins + 1)]
    counts = [0] * bins
    for value in non_null:
        idx = min(int((float(value) - min_val) / step), bins - 1) if step > 0 else 0
        counts[idx] += 1
    return {"bins": edges, "counts": counts}


def analyze_duplicates(frame: pl.DataFrame) -> DuplicateAnalysisDTO:
    total = frame.height
    dup_count = int(frame.is_duplicated().sum()) if total else 0
    pct = round(dup_count / total * 100.0, 2) if total else 0.0
    duplicate_groups: list[tuple[str, ...]] = []
    for col in frame.columns:
        if frame[col].is_duplicated().any():
            duplicate_groups.append((col,))
    return DuplicateAnalysisDTO(
        duplicate_row_count=dup_count,
        duplicate_percentage=pct,
        duplicate_column_groups=tuple(duplicate_groups[:10]),
    )


def analyze_data_quality(frame: pl.DataFrame, settings: Settings) -> DataQualityDTO:
    total = frame.height
    col_count = frame.width
    issues: list[str] = []

    null_pcts = []
    constant_cols: list[str] = []
    near_constant_cols: list[str] = []
    high_card_cols: list[str] = []
    low_card_cols: list[str] = []
    mixed_type_cols: list[str] = []

    for name in frame.columns:
        series = frame[name]
        null_pct = series.null_count() / total * 100.0 if total else 0.0
        null_pcts.append(null_pct)
        non_null = series.drop_nulls()
        distinct = non_null.n_unique() if total else 0

        if distinct <= 1 and total > 0:
            constant_cols.append(name)
            issues.append(f"Column '{name}' is constant.")
        elif total > 0 and distinct / total < 0.01:
            near_constant_cols.append(name)

        if total > 0 and distinct / total > 0.95 and series.dtype == pl.Utf8:
            high_card_cols.append(name)
            issues.append(f"Column '{name}' has very high cardinality — possible identifier.")

        if distinct <= 2 and series.dtype != pl.Boolean:
            low_card_cols.append(name)

        if series.dtype == pl.Utf8:
            numeric_parse = non_null.cast(pl.Float64, strict=False)
            if numeric_parse.null_count() < non_null.len() * 0.5 and non_null.len() > 0:
                mixed_type_cols.append(name)

    avg_null = sum(null_pcts) / len(null_pcts) if null_pcts else 0.0
    completeness = max(0.0, 100.0 - avg_null)

    dup_pct = analyze_duplicates(frame).duplicate_percentage
    uniqueness = max(0.0, 100.0 - dup_pct)

    consistency_penalty = (
        len(constant_cols) * 5 + len(near_constant_cols) * 2 + len(mixed_type_cols) * 4
    )
    consistency = max(0.0, 100.0 - min(100.0, consistency_penalty))

    validity = max(0.0, 100.0 - len(high_card_cols) * 3 - len(mixed_type_cols) * 5)

    integrity_penalty = len(high_card_cols) * 4
    integrity = max(0.0, 100.0 - min(100.0, integrity_penalty))

    weights = settings.quality_score_weights
    overall = (
        completeness * weights["completeness"]
        + uniqueness * weights["uniqueness"]
        + consistency * weights["consistency"]
        + validity * weights["validity"]
        + integrity * weights["integrity"]
    )

    components = (
        ScoreComponentDTO(
            "completeness",
            round(completeness, 1),
            weights["completeness"],
            f"Average missingness is {avg_null:.1f}%.",
        ),
        ScoreComponentDTO(
            "uniqueness",
            round(uniqueness, 1),
            weights["uniqueness"],
            f"Duplicate rows account for {dup_pct:.1f}% of the sample.",
        ),
        ScoreComponentDTO(
            "consistency",
            round(consistency, 1),
            weights["consistency"],
            f"{len(constant_cols)} constant and {len(near_constant_cols)} near-constant columns.",
        ),
        ScoreComponentDTO(
            "validity",
            round(validity, 1),
            weights["validity"],
            "Penalizes mixed types and suspicious high-cardinality text.",
        ),
        ScoreComponentDTO(
            "integrity",
            round(integrity, 1),
            weights["integrity"],
            "Penalizes likely identifier columns without declared keys.",
        ),
    )

    return DataQualityDTO(
        overall_score=round(overall, 1),
        completeness=round(completeness, 1),
        consistency=round(consistency, 1),
        uniqueness=round(uniqueness, 1),
        validity=round(validity, 1),
        integrity=round(integrity, 1),
        duplicate_percentage=dup_pct,
        constant_columns=tuple(constant_cols),
        near_constant_columns=tuple(near_constant_cols),
        high_cardinality_columns=tuple(high_card_cols),
        low_cardinality_columns=tuple(low_card_cols),
        mixed_type_columns=tuple(mixed_type_cols),
        components=components,
        issues=tuple(issues[:20]),
    )


def _suggested_role(
    name: str, semantic: str, distinct: int, total: int, null_pct: float
) -> tuple[str, float, float, list[str], str, float]:
    issues: list[str] = []
    id_prob = 0.0
    target_prob = 0.0
    lower = name.lower()
    if distinct == total and total > 0:
        id_prob = 0.9
        issues.append("All values unique — likely identifier.")
    elif distinct / max(total, 1) > 0.95 and semantic in {"text", "integer"}:
        id_prob = 0.7
        issues.append("Very high uniqueness — review before using as feature.")

    if semantic in {"integer", "float"} and null_pct < 5:
        if any(token in lower for token in ("target", "label", "outcome", "churn", "revenue")):
            target_prob = 0.6

    if null_pct > 50:
        issues.append("More than half the values are missing.")
    if distinct <= 1:
        issues.append("No variation — exclude from modeling.")

    if id_prob >= 0.7:
        role = "identifier"
    elif target_prob >= 0.5:
        role = "target_candidate"
    elif semantic in {"integer", "float"}:
        role = "feature"
    elif semantic == "categorical":
        role = "categorical_feature"
    elif semantic == "datetime":
        role = "temporal"
    elif semantic == "boolean":
        role = "binary_feature"
    else:
        role = "review"

    usability = 100.0
    usability -= min(50.0, null_pct)
    if distinct <= 1:
        usability = 0.0
    elif id_prob >= 0.8:
        usability = max(usability - 40.0, 10.0)

    interpretation = (
        f"{name} behaves as {semantic} data with {distinct} distinct values "
        f"and {null_pct:.1f}% missing."
    )
    return role, id_prob, target_prob, issues, interpretation, max(0.0, min(100.0, usability))


def analyze_columns(frame: pl.DataFrame) -> tuple[ColumnIntelligenceDTO, ...]:
    total = frame.height
    results: list[ColumnIntelligenceDTO] = []

    for name in frame.columns:
        series = frame[name]
        null_pct = round(series.null_count() / total * 100.0, 2) if total else 0.0
        non_null = series.drop_nulls()
        distinct = int(non_null.n_unique()) if total else 0

        dtype = str(series.dtype)
        if _is_numeric(series.dtype):
            semantic = "integer" if series.dtype in {
                pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64
            } else "float"
        elif series.dtype == pl.Boolean:
            semantic = "boolean"
        elif series.dtype in {pl.Date, pl.Datetime, pl.Time}:
            semantic = "datetime"
        elif distinct <= min(50, max(1, total // 10)):
            semantic = "categorical"
        else:
            semantic = "text"

        value_counts = (
            non_null.value_counts(sort=True).head(5) if non_null.len() > 0 else pl.DataFrame()
        )
        top_values: list[dict[str, Any]] = []
        counts: list[int] = []
        if value_counts.height > 0:
            for row in value_counts.iter_rows(named=True):
                col_name = name
                count = int(row["count"])
                counts.append(count)
                top_values.append({col_name: row[col_name], "count": count})

        entropy = _entropy_from_counts(counts, non_null.len())

        minimum = maximum = mean = median = variance = std_dev = skewness = kurtosis = None
        quantiles = None
        mode = None

        if _is_numeric(series.dtype) and non_null.len() > 0:
            num = non_null.cast(pl.Float64)
            minimum = float(num.min())  # type: ignore[arg-type]
            maximum = float(num.max())  # type: ignore[arg-type]
            mean = float(num.mean())  # type: ignore[arg-type]
            median = float(num.median())  # type: ignore[arg-type]
            variance = float(num.var()) if num.len() > 1 else 0.0
            std_dev = float(num.std()) if num.len() > 1 else 0.0
            if num.len() > 2:
                skewness = float(num.skew())  # type: ignore[arg-type]
                kurtosis = float(num.kurtosis())  # type: ignore[arg-type]
            quantiles = {
                "p25": float(num.quantile(0.25)),  # type: ignore[arg-type]
                "p50": float(num.quantile(0.5)),  # type: ignore[arg-type]
                "p75": float(num.quantile(0.75)),  # type: ignore[arg-type]
            }
        elif non_null.len() > 0:
            mode_val = value_counts[name][0] if value_counts.height > 0 else None
            mode = str(mode_val) if mode_val is not None else None

        role, id_prob, target_prob, issues, interpretation, usability = _suggested_role(
            name, semantic, distinct, total, null_pct
        )

        results.append(
            ColumnIntelligenceDTO(
                name=name,
                detected_type=dtype,
                semantic_type=semantic,
                suggested_role=role,
                identifier_probability=round(id_prob, 2),
                target_probability=round(target_prob, 2),
                null_percentage=null_pct,
                distinct_count=distinct,
                entropy=entropy,
                memory_bytes=series.estimated_size(),
                top_values=tuple(top_values),
                minimum=minimum,
                maximum=maximum,
                mean=mean,
                median=median,
                mode=mode,
                variance=variance,
                std_dev=std_dev,
                skewness=skewness,
                kurtosis=kurtosis,
                quantiles=quantiles,
                type_confidence=0.85 if semantic != "text" else 0.7,
                potential_issues=tuple(issues),
                business_interpretation=interpretation,
                usability_score=round(usability, 1),
            )
        )
    return tuple(results)


def analyze_missing_data(frame: pl.DataFrame) -> MissingDataDTO:
    total = frame.height
    col_missing: list[dict[str, Any]] = []
    completely_missing: list[str] = []

    for name in frame.columns:
        null_count = frame[name].null_count()
        pct = round(null_count / total * 100.0, 2) if total else 0.0
        col_missing.append({"column": name, "missing_count": null_count, "missing_percentage": pct})
        if null_count == total and total > 0:
            completely_missing.append(name)

    row_dist: dict[str, int] = {}
    if total > 0:
        row_null_series = frame.select(
            pl.sum_horizontal(pl.all().is_null()).alias("null_count")
        )["null_count"]
        for count in row_null_series:
            key = str(int(count))
            row_dist[key] = row_dist.get(key, 0) + 1

    missing_cols = [c for c in frame.columns if frame[c].null_count() > 0]
    correlations: list[dict[str, Any]] = []
    if len(missing_cols) >= 2:
        for i, col_a in enumerate(missing_cols[:15]):
            for col_b in missing_cols[i + 1 : 15]:
                a = frame[col_a].is_null().cast(pl.Int8)
                b = frame[col_b].is_null().cast(pl.Int8)
                corr = float(frame.select(pl.corr(a, b)).item())  # type: ignore[arg-type]
                if abs(corr) >= 0.3:
                    correlations.append(
                        {"column_a": col_a, "column_b": col_b, "correlation": round(corr, 3)}
                    )

    heatmap_cols = frame.columns[: min(20, frame.width)]
    heatmap_matrix: list[list[float]] = []
    for name in heatmap_cols:
        heatmap_matrix.append(
            [round(frame[name].null_count() / total * 100.0, 2) if total else 0.0]
        )

    overall = (
        sum(item["missing_percentage"] for item in col_missing) / len(col_missing)
        if col_missing
        else 0.0
    )

    hints: list[str] = []
    if completely_missing:
        hints.append("Drop columns that are completely missing.")
    if overall > 20:
        hints.append("Consider row-wise missingness thresholds before modeling.")
    if correlations:
        hints.append("Correlated missingness detected — investigate collection process.")

    return MissingDataDTO(
        overall_missing_percentage=round(overall, 2),
        columns_completely_missing=tuple(completely_missing),
        column_missingness=tuple(col_missing),
        row_missingness_distribution=row_dist,
        missingness_correlations=tuple(correlations),
        heatmap={"columns": heatmap_cols, "values": heatmap_matrix},
        imputation_hints=tuple(hints),
    )


def analyze_outliers(frame: pl.DataFrame, settings: Settings) -> OutlierAnalysisDTO:
    results: list[OutlierColumnDTO] = []
    for name in frame.columns:
        if not _is_numeric(frame[name].dtype):
            continue
        series = frame[name].drop_nulls().cast(pl.Float64)
        if series.len() < 4:
            continue

        q1 = float(series.quantile(0.25))  # type: ignore[arg-type]
        q3 = float(series.quantile(0.75))  # type: ignore[arg-type]
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        iqr_outliers = series.filter((series < lower) | (series > upper))
        iqr_count = iqr_outliers.len()

        mean = float(series.mean())  # type: ignore[arg-type]
        std = float(series.std()) if series.len() > 1 else 0.0  # type: ignore[arg-type]
        z_count = 0
        z_extremes: list[float] = []
        if std > 0:
            z_scores = ((series - mean) / std).abs()
            z_outliers = series.filter(z_scores > settings.outlier_zscore_threshold)
            z_count = z_outliers.len()
            z_extremes = [float(v) for v in z_outliers.head(5).to_list()]

        count = max(iqr_count, z_count)
        pct = round(count / series.len() * 100.0, 2)
        extremes = [float(v) for v in iqr_outliers.head(5).to_list()] or z_extremes

        results.append(
            OutlierColumnDTO(
                column=name,
                method="iqr_and_zscore",
                outlier_count=count,
                outlier_percentage=pct,
                extreme_values=tuple(extremes),
                lower_bound=round(lower, 4),
                upper_bound=round(upper, 4),
            )
        )

    summary = (
        f"Outliers detected in {len(results)} numeric columns using IQR and "
        f"Z-score (threshold={settings.outlier_zscore_threshold})."
    )
    return OutlierAnalysisDTO(columns=tuple(results), summary=summary)


def analyze_distributions(frame: pl.DataFrame) -> tuple[DistributionDTO, ...]:
    distributions: list[DistributionDTO] = []
    for name in frame.columns:
        if not _is_numeric(frame[name].dtype):
            continue
        series = frame[name].drop_nulls().cast(pl.Float64)
        if series.len() == 0:
            continue
        skew = float(series.skew()) if series.len() > 2 else 0.0  # type: ignore[arg-type]
        kurt = float(series.kurtosis()) if series.len() > 2 else 0.0  # type: ignore[arg-type]

        if abs(skew) < 0.5:
            shape = "approximately_symmetric"
        elif skew > 0:
            shape = "right_skewed"
        else:
            shape = "left_skewed"

        normality = "likely_normal" if abs(skew) < 0.5 and abs(kurt) < 1 else "non_normal"
        transforms: list[str] = []
        if shape == "right_skewed":
            transforms.append("log_transform")
        if shape == "left_skewed":
            transforms.append("square_transform")

        q1 = float(series.quantile(0.25))  # type: ignore[arg-type]
        q3 = float(series.quantile(0.75))  # type: ignore[arg-type]
        median = float(series.median())  # type: ignore[arg-type]

        distributions.append(
            DistributionDTO(
                column=name,
                histogram=_histogram_bins(series),
                box_plot={
                    "min": float(series.min()),  # type: ignore[arg-type]
                    "q1": q1,
                    "median": median,
                    "q3": q3,
                    "max": float(series.max()),  # type: ignore[arg-type]
                },
                shape=shape,
                skewness=round(skew, 3),
                kurtosis=round(kurt, 3),
                normality_indicator=normality,
                suggested_transformations=tuple(transforms),
                interpretation=f"{name} is {shape.replace('_', ' ')} with {normality.replace('_', ' ')} tendencies.",
            )
        )
    return tuple(distributions)


def _corr_strength(value: float) -> tuple[str, str]:
    abs_val = abs(value)
    direction = "positive" if value >= 0 else "negative"
    if abs_val >= 0.7:
        strength = "strong"
    elif abs_val >= 0.4:
        strength = "moderate"
    else:
        strength = "weak"
    return strength, direction


def analyze_correlations(frame: pl.DataFrame, settings: Settings) -> CorrelationAnalysisDTO:
    numeric_cols = [c for c in frame.columns if _is_numeric(frame[c].dtype)][
        : settings.intelligence_correlation_max_columns
    ]
    if len(numeric_cols) < 2:
        return CorrelationAnalysisDTO(
            matrix={"columns": [], "values": []},
            heatmap={"columns": [], "values": []},
            strong_positive=(),
            strong_negative=(),
            weak_relationships=(),
            multicollinearity_warnings=(),
        )

    num_frame = frame.select(numeric_cols).cast(pl.Float64, strict=False)
    matrix_values: list[list[float | None]] = []
    pairs: list[CorrelationPairDTO] = []

    for i, col_a in enumerate(numeric_cols):
        row_vals: list[float | None] = []
        for j, col_b in enumerate(numeric_cols):
            if i == j:
                row_vals.append(1.0)
                continue
            pearson_val = num_frame.select(pl.corr(col_a, col_b)).item()
            pearson = float(pearson_val) if pearson_val is not None else None  # type: ignore[arg-type]
            row_vals.append(round(pearson, 4) if pearson is not None else None)

            if i < j and pearson is not None:
                ranked = num_frame.select(
                    pl.corr(pl.col(col_a).rank(), pl.col(col_b).rank())
                ).item()
                spearman = float(ranked) if ranked is not None else None  # type: ignore[arg-type]
                strength, direction = _corr_strength(pearson)
                pair = CorrelationPairDTO(
                    column_a=col_a,
                    column_b=col_b,
                    pearson=round(pearson, 4),
                    spearman=round(spearman, 4) if spearman is not None else None,
                    kendall=None,
                    strength=strength,
                    direction=direction,
                )
                pairs.append(pair)

        matrix_values.append(row_vals)

    strong_pos = tuple(p for p in pairs if p.strength == "strong" and p.direction == "positive")
    strong_neg = tuple(p for p in pairs if p.strength == "strong" and p.direction == "negative")
    weak = tuple(p for p in pairs if p.strength == "weak")

    warnings: list[str] = []
    for col in numeric_cols:
        high_corr = [p for p in pairs if p.strength == "strong" and col in (p.column_a, p.column_b)]
        if len(high_corr) >= 3:
            warnings.append(f"'{col}' is highly correlated with multiple features — multicollinearity risk.")

    return CorrelationAnalysisDTO(
        matrix={"columns": numeric_cols, "values": matrix_values},
        heatmap={"columns": numeric_cols, "values": matrix_values},
        strong_positive=strong_pos[:15],
        strong_negative=strong_neg[:15],
        weak_relationships=weak[:20],
        multicollinearity_warnings=tuple(warnings),
    )


def analyze_feature_relationships(
    frame: pl.DataFrame, correlations: CorrelationAnalysisDTO
) -> tuple[FeatureRelationshipDTO, ...]:
    relationships: list[FeatureRelationshipDTO] = []

    for pair in correlations.strong_positive + correlations.strong_negative:
        if pair.pearson is None:
            continue
        relationships.append(
            FeatureRelationshipDTO(
                relationship_type="numeric_numeric",
                column_a=pair.column_a,
                column_b=pair.column_b,
                strength=abs(pair.pearson),
                pattern=f"{pair.strength} {pair.direction} linear association",
                investigation_note=(
                    "Correlation does not imply causation — worth exploring in domain context."
                ),
            )
        )

    numeric_cols = [c for c in frame.columns if _is_numeric(frame[c].dtype)]
    cat_cols = [
        c
        for c in frame.columns
        if not _is_numeric(frame[c].dtype) and frame[c].dtype != pl.Boolean
    ][:10]

    for num_col in numeric_cols[:10]:
        for cat_col in cat_cols[:5]:
            grouped = frame.group_by(cat_col).agg(pl.col(num_col).mean().alias("mean"))
            if grouped.height < 2:
                continue
            means = grouped["mean"].drop_nulls()
            if means.len() < 2:
                continue
            spread = float(means.max() - means.min())  # type: ignore[arg-type]
            if spread > 0:
                relationships.append(
                    FeatureRelationshipDTO(
                        relationship_type="numeric_categorical",
                        column_a=num_col,
                        column_b=cat_col,
                        strength=min(1.0, spread / (float(means.mean()) + 1e-9)),  # type: ignore[arg-type]
                        pattern="Mean varies across categories",
                        investigation_note="Check for segment effects or confounding.",
                    )
                )

    return tuple(sorted(relationships, key=lambda r: r.strength, reverse=True)[:25])


def schema_summary(frame: pl.DataFrame) -> tuple[dict[str, Any], ...]:
    summary: list[dict[str, Any]] = []
    for name in frame.columns:
        series = frame[name]
        summary.append(
            {
                "name": name,
                "dtype": str(series.dtype),
                "nullable": series.null_count() > 0,
                "null_percentage": round(series.null_count() / frame.height * 100.0, 2)
                if frame.height
                else 0.0,
            }
        )
    return tuple(summary)
