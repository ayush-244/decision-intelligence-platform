"""Causal assumption validation."""

from __future__ import annotations

import polars as pl

from app.application.dto.causal import AssumptionCheckDTO, AssumptionReportDTO
from app.application.services.statistics.data_extractor import is_numeric
from app.domain.value_objects.causal import AssumptionStatus


class CausalAssumptionValidator:
    """Validate causal assumptions and document limitations transparently."""

    def validate(
        self,
        *,
        frame: pl.DataFrame,
        treatment: str,
        outcome: str,
        dag_valid: bool,
        identified: bool,
        adjustment_set: tuple[str, ...],
    ) -> AssumptionReportDTO:
        checks: list[AssumptionCheckDTO] = []

        checks.append(self._check_dag(dag_valid))
        checks.append(self._check_identification(identified))
        checks.append(self._check_sufficient_data(frame, treatment, outcome))
        checks.append(self._check_overlap(frame, treatment))
        checks.append(self._check_positivity(frame, treatment, adjustment_set))
        checks.append(self._check_unconfoundedness(adjustment_set))
        checks.append(self._check_stable_unit(frame))

        failed = [c for c in checks if c.status == AssumptionStatus.FAILED.value]
        return AssumptionReportDTO(
            checks=tuple(checks),
            all_passed=not failed,
            required_assumptions=(
                "Causal Markov condition — no common causes outside DAG",
                "Faithfulness — statistical independences reflect graph structure",
                "SUTVA — no interference between units",
                "Positivity — all treatment levels observed across covariate strata",
                "Correct DAG specification",
            ),
        )

    def _check_dag(self, valid: bool) -> AssumptionCheckDTO:
        return AssumptionCheckDTO(
            name="Valid DAG",
            status=AssumptionStatus.PASSED.value if valid else AssumptionStatus.FAILED.value,
            explanation="DAG must be acyclic and include treatment and outcome." if valid
            else "DAG validation failed — cycles or missing structure.",
            recommendation=None if valid else "Fix DAG cycles before estimating effects.",
        )

    def _check_identification(self, identified: bool) -> AssumptionCheckDTO:
        return AssumptionCheckDTO(
            name="Identifiability",
            status=AssumptionStatus.PASSED.value if identified else AssumptionStatus.FAILED.value,
            explanation="Causal effect is identifiable from observed data." if identified
            else "Effect is not identifiable — no valid adjustment strategy found.",
            recommendation=None if identified else "Revise DAG or collect additional data.",
        )

    def _check_sufficient_data(
        self, frame: pl.DataFrame, treatment: str, outcome: str
    ) -> AssumptionCheckDTO:
        n = frame.height
        missing_t = frame[treatment].null_count() if treatment in frame.columns else n
        missing_y = frame[outcome].null_count() if outcome in frame.columns else n
        ok = n >= 30 and missing_t < n * 0.2 and missing_y < n * 0.2
        return AssumptionCheckDTO(
            name="Sufficient data",
            status=AssumptionStatus.PASSED.value if ok else AssumptionStatus.WARNING.value,
            explanation=f"n={n}, treatment missing={missing_t}, outcome missing={missing_y}.",
            recommendation="Increase sample size if n < 30." if not ok else None,
        )

    def _check_overlap(self, frame: pl.DataFrame, treatment: str) -> AssumptionCheckDTO:
        if treatment not in frame.columns:
            return AssumptionCheckDTO(
                name="Treatment overlap", status=AssumptionStatus.FAILED.value,
                explanation="Treatment column not found.",
            )
        series = frame[treatment].drop_nulls()
        if is_numeric(series.dtype):
            return AssumptionCheckDTO(
                name="Treatment overlap", status=AssumptionStatus.PASSED.value,
                explanation="Continuous treatment — overlap assessed during estimation.",
            )
        counts = series.value_counts()
        min_count = int(counts["count"].min()) if counts.height > 0 else 0
        ok = min_count >= 5
        return AssumptionCheckDTO(
            name="Treatment overlap",
            status=AssumptionStatus.PASSED.value if ok else AssumptionStatus.WARNING.value,
            explanation=f"Minimum treatment group size: {min_count}.",
            recommendation="Small groups reduce estimation reliability." if not ok else None,
        )

    def _check_positivity(
        self, frame: pl.DataFrame, treatment: str, adjustment_set: tuple[str, ...]
    ) -> AssumptionCheckDTO:
        return AssumptionCheckDTO(
            name="Positivity",
            status=AssumptionStatus.NOT_CHECKED.value,
            explanation=(
                "Positivity (every treatment level possible in each covariate stratum) "
                "requires domain review. Automated check is conservative."
            ),
            recommendation="Verify all treatment × covariate combinations have observations.",
        )

    def _check_unconfoundedness(self, adjustment_set: tuple[str, ...]) -> AssumptionCheckDTO:
        if adjustment_set:
            return AssumptionCheckDTO(
                name="Unconfoundedness (conditional)",
                status=AssumptionStatus.NOT_CHECKED.value,
                explanation=(
                    f"Assumes no unmeasured confounders after adjusting for "
                    f"{', '.join(adjustment_set)}. This cannot be verified from data alone."
                ),
            )
        return AssumptionCheckDTO(
            name="Unconfoundedness",
            status=AssumptionStatus.WARNING.value,
            explanation="No adjustment set — unconfoundedness is unlikely without randomization.",
            recommendation="Add confounders to the DAG and adjustment set.",
        )

    def _check_stable_unit(self, frame: pl.DataFrame) -> AssumptionCheckDTO:
        return AssumptionCheckDTO(
            name="SUTVA",
            status=AssumptionStatus.NOT_CHECKED.value,
            explanation=(
                "Stable Unit Treatment Value Assumption — no interference between units. "
                "Requires knowledge of data collection design."
            ),
        )
