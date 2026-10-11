"""Business constraint evaluation."""

from __future__ import annotations

from app.application.dto.simulation import (
    ConstraintDTO,
    ConstraintEvaluationDTO,
    CounterfactualOutcomeDTO,
    ROIEstimateDTO,
)
from app.domain.value_objects.simulation import ConstraintType


class ConstraintEngine:
    """Evaluate hard and soft business constraints against simulation outputs."""

    def evaluate(
        self,
        *,
        constraints: tuple[ConstraintDTO, ...],
        counterfactual: CounterfactualOutcomeDTO,
        roi: ROIEstimateDTO,
    ) -> tuple[ConstraintEvaluationDTO, ...]:
        results: list[ConstraintEvaluationDTO] = []
        for constraint in constraints:
            results.append(self._evaluate_one(constraint, counterfactual, roi))
        return tuple(results)

    def _evaluate_one(
        self,
        constraint: ConstraintDTO,
        counterfactual: CounterfactualOutcomeDTO,
        roi: ROIEstimateDTO,
    ) -> ConstraintEvaluationDTO:
        ctype = constraint.type
        threshold = constraint.threshold

        if ctype == ConstraintType.MAX_BUDGET.value and threshold is not None:
            actual = roi.expected_cost
            satisfied = actual <= threshold
            return ConstraintEvaluationDTO(
                constraint=constraint,
                satisfied=satisfied,
                actual_value=actual,
                message=(
                    f"Expected cost {actual:.2f} {'within' if satisfied else 'exceeds'} "
                    f"budget {threshold:.2f}."
                ),
            )

        if ctype == ConstraintType.MIN_ROI.value and threshold is not None:
            actual = roi.expected_roi
            satisfied = actual >= threshold
            return ConstraintEvaluationDTO(
                constraint=constraint,
                satisfied=satisfied,
                actual_value=actual,
                message=(
                    f"Expected ROI {actual:.2%} {'meets' if satisfied else 'below'} "
                    f"minimum {threshold:.2%}."
                ),
            )

        if ctype == ConstraintType.CAPACITY.value and threshold is not None:
            delta = abs(counterfactual.expected_treatment_effect)
            satisfied = delta <= threshold
            return ConstraintEvaluationDTO(
                constraint=constraint,
                satisfied=satisfied,
                actual_value=delta,
                message=f"Treatment effect magnitude {delta:.4g} vs capacity {threshold:.4g}.",
            )

        return ConstraintEvaluationDTO(
            constraint=constraint,
            satisfied=True,
            actual_value=None,
            message=constraint.description or f"Constraint '{ctype}' recorded for review.",
        )
