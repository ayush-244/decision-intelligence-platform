"""Unit tests for data intelligence analyzers."""

from __future__ import annotations

import polars as pl
import pytest

from app.application.services.intelligence.analyzers import (
    analyze_columns,
    analyze_correlations,
    analyze_data_quality,
    analyze_duplicates,
    analyze_missing_data,
    analyze_outliers,
)
from app.core.config import Environment, LogFormat, Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        environment=Environment.DEVELOPMENT,
        debug=False,
        log_format=LogFormat.CONSOLE,
        cors_origins=[],
    )


@pytest.fixture
def sample_frame() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "category": ["a", "b", "a", "c", "b"],
            "value": [10.0, 20.0, None, 100.0, 22.0],
            "constant": [1, 1, 1, 1, 1],
        }
    )


def test_analyze_duplicates_detects_none_in_unique_rows(sample_frame: pl.DataFrame) -> None:
    result = analyze_duplicates(sample_frame)
    assert result.duplicate_row_count == 0


def test_analyze_data_quality_flags_constant_column(
    sample_frame: pl.DataFrame, settings: Settings
) -> None:
    result = analyze_data_quality(sample_frame, settings)
    assert "constant" in result.constant_columns
    assert 0 <= result.overall_score <= 100


def test_analyze_columns_returns_metadata(sample_frame: pl.DataFrame) -> None:
    columns = analyze_columns(sample_frame)
    names = {col.name for col in columns}
    assert names == {"id", "category", "value", "constant"}
    value_col = next(col for col in columns if col.name == "value")
    assert value_col.null_percentage == 20.0


def test_analyze_missing_data(sample_frame: pl.DataFrame) -> None:
    result = analyze_missing_data(sample_frame)
    assert result.overall_missing_percentage > 0
    value_missing = next(
        item for item in result.column_missingness if item["column"] == "value"
    )
    assert value_missing["missing_count"] == 1


def test_analyze_outliers_detects_extreme_value(settings: Settings) -> None:
    frame = pl.DataFrame({"amount": [1.0, 2.0, 3.0, 4.0, 1000.0]})
    result = analyze_outliers(frame, settings)
    assert len(result.columns) == 1
    assert result.columns[0].outlier_count >= 1


def test_analyze_correlations_numeric_pairs(settings: Settings) -> None:
    frame = pl.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 4, 6, 8, 10], "c": [5, 4, 3, 2, 1]})
    result = analyze_correlations(frame, settings)
    assert len(result.matrix["columns"]) == 3
    assert len(result.strong_positive) >= 1
