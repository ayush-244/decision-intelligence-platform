"""Unit tests for statistical executors — validated against scipy reference values."""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest
from scipy import stats

from app.application.dto.statistics import VariableSpecDTO
from app.application.services.statistics.data_extractor import AnalysisDataExtractor
from app.application.services.statistics.effect_sizes import EffectSizeCalculator
from app.application.services.statistics.executors import StatisticalExecutor
from app.domain.value_objects.statistics import StatisticalTestType


@pytest.fixture
def executor() -> StatisticalExecutor:
    return StatisticalExecutor()


def test_independent_ttest_matches_scipy(executor: StatisticalExecutor) -> None:
    rng = np.random.default_rng(42)
    g1 = rng.normal(10, 2, 30)
    g2 = rng.normal(12, 2, 35)
    frame = pl.DataFrame({"outcome": np.concatenate([g1, g2]), "group": ["A"] * 30 + ["B"] * 35})
    extracted = AnalysisDataExtractor().extract(
        frame,
        (VariableSpecDTO("outcome", "outcome"), VariableSpecDTO("group", "grouping")),
    )
    result, _ = executor.execute(
        test_type=StatisticalTestType.INDEPENDENT_TTEST,
        frame=frame,
        extracted=extracted,
        alpha=0.05,
    )
    scipy_stat, scipy_p = stats.ttest_ind(g1, g2, equal_var=True)
    assert result.p_value == pytest.approx(float(scipy_p), rel=1e-5)
    assert result.statistic == pytest.approx(float(scipy_stat), rel=1e-5)


def test_pearson_correlation_matches_scipy(executor: StatisticalExecutor) -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    y = np.array([2.0, 4.0, 5.0, 4.0, 5.0])
    frame = pl.DataFrame({"x": x, "y": y})
    extracted = AnalysisDataExtractor().extract(
        frame,
        (VariableSpecDTO("y", "outcome"), VariableSpecDTO("x", "predictor")),
    )
    result, details = executor.execute(
        test_type=StatisticalTestType.PEARSON_CORRELATION,
        frame=frame,
        extracted=extracted,
        alpha=0.05,
    )
    scipy_r, scipy_p = stats.pearsonr(x, y)
    assert result.statistic == pytest.approx(float(scipy_r), rel=1e-5)
    assert result.p_value == pytest.approx(float(scipy_p), rel=1e-5)
    assert details["correlation"] == pytest.approx(float(scipy_r), rel=1e-5)


def test_cohens_d_effect_size() -> None:
    g1 = np.array([1.0, 2.0, 3.0, 4.0])
    g2 = np.array([3.0, 4.0, 5.0, 6.0])
    frame = pl.DataFrame({"outcome": np.concatenate([g1, g2]), "group": ["A"] * 4 + ["B"] * 4})
    extracted = AnalysisDataExtractor().extract(
        frame,
        (VariableSpecDTO("outcome", "outcome"), VariableSpecDTO("group", "grouping")),
    )
    effects = EffectSizeCalculator().compute(
        test_type=StatisticalTestType.INDEPENDENT_TTEST,
        extracted=extracted,
    )
    assert len(effects) >= 1
    assert effects[0].name == "cohens_d"
    assert effects[0].value < 0  # g1 mean < g2 mean
