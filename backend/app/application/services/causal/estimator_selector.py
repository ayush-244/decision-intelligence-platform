"""Estimator selection for causal treatment effects."""

from __future__ import annotations

import polars as pl

from app.application.dto.causal import IdentificationReportDTO
from app.domain.value_objects.causal import CausalEstimatorType, IdentificationStrategy


class EstimatorSelector:
    """Recommend estimators based on data characteristics and identification."""

    def select(
        self,
        *,
        frame: pl.DataFrame,
        treatment: str,
        identification: IdentificationReportDTO,
        preferred: CausalEstimatorType | None = None,
    ) -> tuple[CausalEstimatorType, str]:
        if preferred is not None:
            return preferred, f"User-selected estimator: {preferred.value}."

        if not identification.identified:
            return (
                CausalEstimatorType.DIFFERENCE_IN_MEANS,
                "Identification failed — reporting naive difference (NOT causal). Clearly labeled.",
            )

        n = frame.height
        treatment_col = frame[treatment].drop_nulls()
        is_binary = treatment_col.n_unique() == 2
        n_adjust = len(identification.adjustment_set)

        if identification.strategy is IdentificationStrategy.BACKDOOR:
            if is_binary and n < 500:
                return (
                    CausalEstimatorType.PROPENSITY_SCORE_MATCHING,
                    "Binary treatment with moderate sample — propensity score matching balances groups.",
                )
            if is_binary and n >= 500:
                return (
                    CausalEstimatorType.INVERSE_PROBABILITY_WEIGHTING,
                    "Binary treatment with larger sample — IPW is efficient and interpretable.",
                )
            if n_adjust > 0 and n >= 100:
                return (
                    CausalEstimatorType.REGRESSION_ADJUSTMENT,
                    f"Adjusting for {n_adjust} confounders via regression.",
                )
            return (
                CausalEstimatorType.DIFFERENCE_IN_MEANS,
                "Simple adjusted difference — verify overlap assumptions.",
            )

        return (
            CausalEstimatorType.DIFFERENCE_IN_MEANS,
            "Default estimator — review identification report.",
        )
