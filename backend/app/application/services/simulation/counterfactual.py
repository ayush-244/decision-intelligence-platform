"""Counterfactual outcome generation from causal treatment effects."""

from __future__ import annotations

import polars as pl

from app.application.dto.causal import TreatmentEffectDTO
from app.application.dto.simulation import CounterfactualOutcomeDTO, InterventionDTO
from app.domain.value_objects.simulation import InterventionMode


class CounterfactualGenerator:
    """Estimate counterfactual outcomes using causal ATE and intervention deltas."""

    def generate(
        self,
        *,
        frame: pl.DataFrame,
        treatment: str,
        outcome: str,
        treatment_effect: TreatmentEffectDTO,
        interventions: tuple[InterventionDTO, ...],
        confidence_level: float,
    ) -> CounterfactualOutcomeDTO:
        outcome_series = frame[outcome].cast(pl.Float64).drop_nulls()
        baseline_outcome = float(outcome_series.mean())  # type: ignore[arg-type]

        treatment_series = frame[treatment].drop_nulls()
        baseline_treatment = self._baseline_treatment_value(treatment_series)
        projected_treatment = self._apply_interventions(
            baseline_treatment, treatment, interventions, treatment_series
        )
        delta_treatment = projected_treatment - baseline_treatment

        ate = treatment_effect.ate or treatment_effect.att or 0.0
        std_error = treatment_effect.std_error or abs(ate) * 0.25 or 1.0
        expected_effect = ate * self._effect_scale(delta_treatment, baseline_treatment)
        expected_outcome = baseline_outcome + expected_effect

        z = 1.96 if confidence_level >= 0.95 else 1.645
        ci_lower = expected_outcome - z * std_error
        ci_upper = expected_outcome + z * std_error

        improvement_prob = self._normal_cdf(expected_effect / std_error) if std_error > 0 else 0.5
        deterioration_prob = 1.0 - improvement_prob
        uncertainty = min(1.0, std_error / (abs(expected_effect) + 1e-6))

        warnings: list[str] = []
        if abs(delta_treatment) > abs(baseline_treatment) * 0.5:
            warnings.append(
                "Large intervention relative to baseline treatment — extrapolation beyond observed data."
            )
        if not treatment_effect.ate and not treatment_effect.att:
            warnings.append("Causal model did not provide a reliable ATE/ATT estimate.")

        return CounterfactualOutcomeDTO(
            baseline_outcome=baseline_outcome,
            expected_outcome=expected_outcome,
            expected_treatment_effect=expected_effect,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            probability_improvement=round(improvement_prob, 4),
            probability_deterioration=round(deterioration_prob, 4),
            uncertainty_score=round(uncertainty, 4),
            extrapolation_warnings=tuple(warnings),
        )

    @staticmethod
    def _baseline_treatment_value(series: pl.Series) -> float:
        if series.dtype == pl.Boolean:
            return float(series.cast(pl.Float64).mean())  # type: ignore[arg-type]
        if series.dtype in {pl.Float64, pl.Float32, pl.Int64, pl.Int32}:
            return float(series.cast(pl.Float64).mean())  # type: ignore[arg-type]
        return 1.0

    @staticmethod
    def _apply_interventions(
        baseline: float,
        treatment: str,
        interventions: tuple[InterventionDTO, ...],
        treatment_series: pl.Series,
    ) -> float:
        projected = baseline
        for intervention in interventions:
            if intervention.variable != treatment:
                continue
            value = intervention.value
            if intervention.mode == InterventionMode.RELATIVE.value and isinstance(value, (int, float)):
                projected = baseline * (1 + float(value))
            elif intervention.mode == InterventionMode.ABSOLUTE.value and isinstance(value, (int, float)):
                projected = baseline + float(value)
            elif intervention.mode == InterventionMode.SET_VALUE.value and isinstance(value, (int, float)):
                projected = float(value)
            elif intervention.mode == InterventionMode.TOGGLE.value:
                projected = 1.0 if value else 0.0
        if projected == baseline and treatment_series.dtype in {pl.Float64, pl.Int32, pl.Int64}:
            col_max = float(treatment_series.cast(pl.Float64).max())  # type: ignore[arg-type]
            col_min = float(treatment_series.cast(pl.Float64).min())  # type: ignore[arg-type]
            if col_max > col_min:
                projected = (col_min + col_max) / 2
        return projected

    @staticmethod
    def _effect_scale(delta: float, baseline: float) -> float:
        if abs(baseline) < 1e-9:
            return delta
        return delta / baseline

    @staticmethod
    def _normal_cdf(x: float) -> float:
        from math import erf, sqrt

        return 0.5 * (1.0 + erf(x / sqrt(2.0)))
