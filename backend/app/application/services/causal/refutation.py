"""Refutation engine — test robustness of causal estimates."""

from __future__ import annotations

import numpy as np
import polars as pl

from app.application.dto.causal import RefutationResultDTO, TreatmentEffectDTO
from app.application.services.causal.treatment_effects import TreatmentEffectEngine
from app.domain.value_objects.causal import CausalEstimatorType, RefutationMethod


class RefutationEngine:
    """Run refutation tests to assess estimate robustness."""

    def __init__(self) -> None:
        self._effects = TreatmentEffectEngine()

    def refute(
        self,
        *,
        frame: pl.DataFrame,
        treatment: str,
        outcome: str,
        original: TreatmentEffectDTO,
        adjustment_set: tuple[str, ...],
        methods: tuple[RefutationMethod, ...] | None = None,
    ) -> tuple[RefutationResultDTO, ...]:
        methods = methods or (
            RefutationMethod.RANDOM_COMMON_CAUSE,
            RefutationMethod.PLACEBO_TREATMENT,
            RefutationMethod.SUBSET_VALIDATION,
        )
        results: list[RefutationResultDTO] = []
        orig_ate = original.ate or 0.0

        for method in methods:
            if method is RefutationMethod.RANDOM_COMMON_CAUSE:
                results.append(self._random_common_cause(
                    frame, treatment, outcome, adjustment_set, orig_ate, original.estimator
                ))
            elif method is RefutationMethod.PLACEBO_TREATMENT:
                results.append(self._placebo_treatment(
                    frame, treatment, outcome, adjustment_set, orig_ate, original.estimator
                ))
            elif method in {RefutationMethod.SUBSET_VALIDATION, RefutationMethod.DATA_SUBSET}:
                results.append(self._subset_validation(
                    frame, treatment, outcome, adjustment_set, orig_ate, original.estimator
                ))
            elif method is RefutationMethod.BOOTSTRAP:
                results.append(self._bootstrap_validation(
                    frame, treatment, outcome, adjustment_set, orig_ate, original.estimator
                ))
        return tuple(results)

    def _random_common_cause(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], orig_ate: float, estimator: CausalEstimatorType,
    ) -> RefutationResultDTO:
        rng = np.random.default_rng(42)
        noise = rng.normal(0, 1, frame.height)
        augmented = frame.with_columns(pl.Series("_random_confounder", noise))
        new_adj = adjustment_set + ("_random_confounder",)
        try:
            result = self._effects.estimate(
                frame=augmented, treatment=treatment, outcome=outcome,
                estimator=estimator, adjustment_set=new_adj,
            )
            refuted = result.ate or 0.0
            change = abs(refuted - orig_ate)
            passed = change < abs(orig_ate) * 0.5 + 0.01
            return RefutationResultDTO(
                method=RefutationMethod.RANDOM_COMMON_CAUSE.value,
                original_effect=orig_ate, refuted_effect=refuted, passed=passed,
                explanation=(
                    f"Adding random confounder changed ATE by {change:.4f}. "
                    f"{'Estimate is stable' if passed else 'Estimate is sensitive to spurious covariates'}."
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return RefutationResultDTO(
                method=RefutationMethod.RANDOM_COMMON_CAUSE.value,
                original_effect=orig_ate, refuted_effect=0.0, passed=False,
                explanation=f"Refutation failed: {exc}",
            )

    def _placebo_treatment(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], orig_ate: float, estimator: CausalEstimatorType,
    ) -> RefutationResultDTO:
        rng = np.random.default_rng(123)
        shuffled = frame[treatment].to_numpy().copy()
        rng.shuffle(shuffled)
        placebo_frame = frame.with_columns(pl.Series(treatment, shuffled))
        try:
            result = self._effects.estimate(
                frame=placebo_frame, treatment=treatment, outcome=outcome,
                estimator=estimator, adjustment_set=adjustment_set,
            )
            refuted = result.ate or 0.0
            passed = abs(refuted) < abs(orig_ate) * 0.3 + 0.05
            return RefutationResultDTO(
                method=RefutationMethod.PLACEBO_TREATMENT.value,
                original_effect=orig_ate, refuted_effect=refuted, passed=passed,
                explanation=(
                    f"Placebo (shuffled) treatment ATE = {refuted:.4f}. "
                    f"{'Consistent with no spurious effect' if passed else 'Possible spurious association detected'}."
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return RefutationResultDTO(
                method=RefutationMethod.PLACEBO_TREATMENT.value,
                original_effect=orig_ate, refuted_effect=0.0, passed=False,
                explanation=f"Placebo refutation failed: {exc}",
            )

    def _subset_validation(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], orig_ate: float, estimator: CausalEstimatorType,
    ) -> RefutationResultDTO:
        half = frame.head(frame.height // 2)
        try:
            result = self._effects.estimate(
                frame=half, treatment=treatment, outcome=outcome,
                estimator=estimator, adjustment_set=adjustment_set,
            )
            refuted = result.ate or 0.0
            passed = abs(refuted - orig_ate) < abs(orig_ate) * 0.5 + 0.1
            return RefutationResultDTO(
                method=RefutationMethod.SUBSET_VALIDATION.value,
                original_effect=orig_ate, refuted_effect=refuted, passed=passed,
                explanation=(
                    f"Half-sample ATE = {refuted:.4f} vs full-sample {orig_ate:.4f}. "
                    f"{'Directionally consistent' if passed else 'Substantial variation across subsets'}."
                ),
            )
        except Exception as exc:  # noqa: BLE001
            return RefutationResultDTO(
                method=RefutationMethod.SUBSET_VALIDATION.value,
                original_effect=orig_ate, refuted_effect=0.0, passed=False,
                explanation=f"Subset refutation failed: {exc}",
            )

    def _bootstrap_validation(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], orig_ate: float, estimator: CausalEstimatorType,
    ) -> RefutationResultDTO:
        rng = np.random.default_rng(99)
        boot_ates: list[float] = []
        for _ in range(50):
            idx = rng.choice(frame.height, frame.height, replace=True)
            sample = frame[idx.tolist()] if hasattr(frame, "__getitem__") else frame.sample(fraction=1.0, with_replacement=True)
            try:
                sub = pl.DataFrame([frame.row(i, named=True) for i in idx])
                result = self._effects.estimate(
                    frame=sub, treatment=treatment, outcome=outcome,
                    estimator=estimator, adjustment_set=adjustment_set,
                )
                boot_ates.append(result.ate or 0.0)
            except Exception:  # noqa: BLE001
                continue
        if not boot_ates:
            return RefutationResultDTO(
                method=RefutationMethod.BOOTSTRAP.value,
                original_effect=orig_ate, refuted_effect=0.0, passed=False,
                explanation="Bootstrap refutation could not complete.",
            )
        median = float(np.median(boot_ates))
        passed = abs(median - orig_ate) < abs(orig_ate) * 0.3 + 0.05
        return RefutationResultDTO(
            method=RefutationMethod.BOOTSTRAP.value,
            original_effect=orig_ate, refuted_effect=median, passed=passed,
            explanation=f"Bootstrap median ATE = {median:.4f} (50 resamples).",
        )
