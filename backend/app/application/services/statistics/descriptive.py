"""Descriptive statistics computation."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl
from scipy import stats

from app.application.services.statistics.data_extractor import is_numeric


class DescriptiveStatistics:
    """Compute summary statistics for numeric and categorical columns."""

    def compute(self, frame: pl.DataFrame, columns: list[str] | None = None) -> dict[str, Any]:
        target_cols = columns or list(frame.columns)
        numeric_summaries: list[dict[str, Any]] = []
        categorical_summaries: list[dict[str, Any]] = []

        for col in target_cols:
            if col not in frame.columns:
                continue
            series = frame[col]
            if is_numeric(series.dtype):
                numeric_summaries.append(self._numeric_summary(series))
            else:
                categorical_summaries.append(self._categorical_summary(series))

        return {
            "numeric": numeric_summaries,
            "categorical": categorical_summaries,
            "row_count": frame.height,
            "column_count": len(target_cols),
        }

    def _numeric_summary(self, series: pl.Series) -> dict[str, Any]:
        data = series.drop_nulls().cast(pl.Float64).to_numpy()
        if len(data) == 0:
            return {"column": series.name, "count": 0}
        return {
            "column": series.name,
            "count": int(len(data)),
            "missing": int(series.null_count()),
            "mean": float(np.mean(data)),
            "std": float(np.std(data, ddof=1)) if len(data) > 1 else 0.0,
            "min": float(np.min(data)),
            "q25": float(np.percentile(data, 25)),
            "median": float(np.median(data)),
            "q75": float(np.percentile(data, 75)),
            "max": float(np.max(data)),
            "skewness": float(stats.skew(data)) if len(data) > 2 else None,
            "kurtosis": float(stats.kurtosis(data)) if len(data) > 3 else None,
        }

    def _categorical_summary(self, series: pl.Series) -> dict[str, Any]:
        non_null = series.drop_nulls()
        counts = non_null.value_counts().sort("count", descending=True)
        top = [
            {"value": str(row[series.name]), "count": int(row["count"])}
            for row in counts.head(10).iter_rows(named=True)
        ]
        return {
            "column": series.name,
            "count": int(non_null.len()),
            "missing": int(series.null_count()),
            "unique": int(non_null.n_unique()),
            "top_values": top,
        }
