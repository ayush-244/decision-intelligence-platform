"""Intervention validation before simulation."""

from __future__ import annotations

import polars as pl

from app.application.dto.simulation import InterventionDTO, InterventionValidationDTO
from app.domain.value_objects.simulation import InterventionMode


class InterventionValidator:
    """Validate interventions against observed data and column types."""

    def validate(
        self,
        *,
        frame: pl.DataFrame,
        interventions: tuple[InterventionDTO, ...],
        treatment: str,
    ) -> InterventionValidationDTO:
        errors: list[str] = []
        warnings: list[str] = []

        for intervention in interventions:
            var = intervention.variable
            if var not in frame.columns:
                errors.append(f"Variable '{var}' not found in dataset.")
                continue

            series = frame[var].drop_nulls()
            if len(series) == 0:
                errors.append(f"Variable '{var}' has no non-null values.")
                continue

            dtype = frame[var].dtype
            is_numeric = dtype in {pl.Float64, pl.Float32, pl.Int64, pl.Int32, pl.UInt32}
            is_bool = dtype == pl.Boolean
            is_categorical = dtype == pl.Utf8 or dtype == pl.Categorical

            mode = intervention.mode
            value = intervention.value

            if mode == InterventionMode.TOGGLE.value:
                if not is_bool and not is_numeric:
                    errors.append(f"Toggle intervention on '{var}' requires boolean or binary column.")
            elif mode == InterventionMode.SET_VALUE.value:
                if is_numeric and not isinstance(value, (int, float)):
                    errors.append(f"Set-value on numeric '{var}' requires a number.")
                elif is_categorical and not isinstance(value, str):
                    errors.append(f"Set-value on categorical '{var}' requires a string.")
            elif mode in {InterventionMode.ABSOLUTE.value, InterventionMode.RELATIVE.value}:
                if not is_numeric:
                    errors.append(f"Absolute/relative intervention on '{var}' requires numeric column.")
                elif isinstance(value, (int, float)):
                    if is_numeric:
                        col_min = float(series.min())  # type: ignore[arg-type]
                        col_max = float(series.max())  # type: ignore[arg-type]
                        baseline = float(series.mean())  # type: ignore[arg-type]
                        projected = self._project_value(baseline, mode, float(value))
                        if projected < col_min * 0.5 or projected > col_max * 1.5:
                            warnings.append(
                                f"Intervention on '{var}' extrapolates beyond observed range "
                                f"({col_min:.4g}–{col_max:.4g}). Simulation uncertainty increases."
                            )

            if var != treatment and var not in errors:
                warnings.append(
                    f"Intervention on '{var}' is not the causal treatment '{treatment}'. "
                    "Effect estimates may not apply directly."
                )

        return InterventionValidationDTO(
            valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _project_value(baseline: float, mode: str, value: float) -> float:
        if mode == InterventionMode.RELATIVE.value:
            return baseline * (1 + value)
        return baseline + value
