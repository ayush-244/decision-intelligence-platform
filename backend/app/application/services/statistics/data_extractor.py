"""Extract analysis-ready arrays from Polars frames."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from app.application.dto.statistics import VariableSpecDTO
from app.shared.exceptions import BusinessValidationError

_NUMERIC = {
    pl.Int8, pl.Int16, pl.Int32, pl.Int64,
    pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
    pl.Float32, pl.Float64,
}


def is_numeric(dtype: pl.DataType) -> bool:
    return dtype in _NUMERIC


@dataclass(frozen=True, slots=True)
class ExtractedData:
    outcome: np.ndarray | None
    predictor: np.ndarray | None
    grouping: np.ndarray | None
    covariates: dict[str, np.ndarray]
    outcome_name: str | None
    predictor_name: str | None
    grouping_name: str | None


class AnalysisDataExtractor:
    """Map variable roles to numpy arrays for scipy/statsmodels."""

    def extract(self, frame: pl.DataFrame, variables: tuple[VariableSpecDTO, ...]) -> ExtractedData:
        outcome = predictor = grouping = None
        outcome_name = predictor_name = grouping_name = None
        covariates: dict[str, np.ndarray] = {}

        for spec in variables:
            if spec.name not in frame.columns:
                raise BusinessValidationError(f"Column '{spec.name}' not found in dataset.")
            series = frame[spec.name]
            if spec.role == "outcome":
                outcome, outcome_name = self._numeric_array(series), spec.name
            elif spec.role == "predictor":
                predictor, predictor_name = self._to_array(series), spec.name
            elif spec.role == "grouping":
                grouping, grouping_name = self._to_array(series), spec.name
            elif spec.role == "covariate":
                covariates[spec.name] = self._numeric_array(series)

        return ExtractedData(
            outcome=outcome,
            predictor=predictor,
            grouping=grouping,
            covariates=covariates,
            outcome_name=outcome_name,
            predictor_name=predictor_name,
            grouping_name=grouping_name,
        )

    @staticmethod
    def _numeric_array(series: pl.Series) -> np.ndarray:
        if not is_numeric(series.dtype):
            converted = series.cast(pl.Float64, strict=False)
            if converted.null_count() == series.len():
                raise BusinessValidationError(f"Column '{series.name}' is not numeric.")
            return converted.drop_nulls().to_numpy()
        return series.drop_nulls().cast(pl.Float64).to_numpy()

    @staticmethod
    def _to_array(series: pl.Series) -> np.ndarray:
        return series.drop_nulls().to_numpy()
