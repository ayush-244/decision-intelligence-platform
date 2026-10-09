"""Regression diagnostics and visualization data."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from app.application.dto.statistics import RegressionDiagnosticsDTO
from app.application.services.statistics.data_extractor import ExtractedData, is_numeric
from app.domain.value_objects.statistics import StatisticalTestType


class RegressionEngine:
    """Build regression diagnostics for result explorer and regression viewer."""

    def build_diagnostics(
        self,
        *,
        test_type: StatisticalTestType,
        frame: pl.DataFrame,
        extracted: ExtractedData,
        execution_details: dict[str, Any],
    ) -> RegressionDiagnosticsDTO | None:
        if test_type not in {
            StatisticalTestType.SIMPLE_LINEAR_REGRESSION,
            StatisticalTestType.MULTIPLE_LINEAR_REGRESSION,
            StatisticalTestType.LOGISTIC_REGRESSION,
        }:
            return None

        coefficients = tuple(execution_details.get("coefficients", []))
        vif = self._compute_vif(test_type, frame, extracted)
        residual_summary = self._residual_summary(execution_details)

        return RegressionDiagnosticsDTO(
            r_squared=execution_details.get("r_squared"),
            adj_r_squared=execution_details.get("adj_r_squared"),
            coefficients=coefficients,
            vif=vif,
            residual_summary=residual_summary,
        )

    def visualization_data(
        self,
        *,
        test_type: StatisticalTestType,
        frame: pl.DataFrame,
        extracted: ExtractedData,
        execution_details: dict[str, Any],
    ) -> dict[str, Any]:
        if test_type is StatisticalTestType.SIMPLE_LINEAR_REGRESSION:
            return self._simple_regression_plots(frame, extracted, execution_details)
        if test_type is StatisticalTestType.MULTIPLE_LINEAR_REGRESSION:
            return self._multiple_regression_plots(frame, extracted, execution_details)
        return {}

    def _compute_vif(
        self, test_type: StatisticalTestType, frame: pl.DataFrame, extracted: ExtractedData
    ) -> tuple[dict[str, Any], ...]:
        if test_type is not StatisticalTestType.MULTIPLE_LINEAR_REGRESSION:
            return ()
        names = []
        if extracted.predictor_name:
            names.append(extracted.predictor_name)
        names.extend(extracted.covariates.keys())
        if len(names) < 2:
            return ()
        x_df = frame.select(names).drop_nulls().cast(pl.Float64)
        if x_df.height < len(names) + 1:
            return ()
        x = x_df.to_numpy()
        x_const = sm.add_constant(x)
        results = []
        for i, name in enumerate(names):
            try:
                vif_val = float(variance_inflation_factor(x_const, i + 1))
                status = "acceptable" if vif_val < 5 else ("moderate" if vif_val < 10 else "severe")
                results.append({"predictor": name, "vif": vif_val, "status": status})
            except (ValueError, FloatingPointError):
                results.append({"predictor": name, "vif": None, "status": "undefined"})
        return tuple(results)

    @staticmethod
    def _residual_summary(details: dict[str, Any]) -> dict[str, Any]:
        return {
            "residual_std": details.get("residual_std"),
            "note": "Examine residual plots for homoscedasticity and normality.",
        }

    def _simple_regression_plots(
        self, frame: pl.DataFrame, extracted: ExtractedData, details: dict[str, Any]
    ) -> dict[str, Any]:
        if extracted.outcome_name is None or extracted.predictor_name is None:
            return {}
        df = frame.select([extracted.outcome_name, extracted.predictor_name]).drop_nulls().cast(pl.Float64)
        x = df[extracted.predictor_name].to_numpy()
        y = df[extracted.outcome_name].to_numpy()
        if len(x) < 2:
            return {}
        coefs = details.get("coefficients", [])
        intercept = coefs[0]["estimate"] if coefs else 0.0
        slope = coefs[1]["estimate"] if len(coefs) > 1 else 0.0
        x_line = np.linspace(x.min(), x.max(), 50)
        y_line = intercept + slope * x_line
        return {
            "scatter": {
                "x": x.tolist(),
                "y": y.tolist(),
                "x_label": extracted.predictor_name,
                "y_label": extracted.outcome_name,
            },
            "fit_line": {"x": x_line.tolist(), "y": y_line.tolist()},
            "residuals": self._residual_points(x, y, intercept, slope),
        }

    def _multiple_regression_plots(
        self, frame: pl.DataFrame, extracted: ExtractedData, details: dict[str, Any]
    ) -> dict[str, Any]:
        return {"note": "Partial regression plots available in future release."}

    @staticmethod
    def _residual_points(x: np.ndarray, y: np.ndarray, intercept: float, slope: float) -> dict[str, Any]:
        fitted = intercept + slope * x
        resid = y - fitted
        return {"fitted": fitted.tolist(), "residuals": resid.tolist()}
