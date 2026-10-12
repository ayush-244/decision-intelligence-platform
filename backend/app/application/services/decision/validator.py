"""Validate recommendations against evidence thresholds."""

from __future__ import annotations

from app.application.dto.decision import RecommendationDTO
from app.domain.value_objects.decision import RecommendationStatus


class DecisionValidator:
    """Reject recommendations that cannot be defended with evidence."""

    def validate(
        self,
        *,
        recommendation: RecommendationDTO,
        min_confidence: float,
        risk_tolerance: float,
        constraints_satisfied: bool,
        causal_identified: bool,
    ) -> tuple[bool, str, str]:
        notes: list[str] = []
        passed = True

        if recommendation.confidence < min_confidence:
            passed = False
            notes.append(
                f"Confidence {recommendation.confidence:.0%} below threshold {min_confidence:.0%}."
            )
        if recommendation.risk > risk_tolerance:
            passed = False
            notes.append(
                f"Risk {recommendation.risk:.0%} exceeds tolerance {risk_tolerance:.0%}."
            )
        if not constraints_satisfied:
            passed = False
            notes.append("One or more hard business constraints are violated.")
        if not causal_identified:
            notes.append("Causal identification was not confirmed — recommendation is conditional.")
            if recommendation.confidence < 0.6:
                passed = False

        if passed and notes:
            status = RecommendationStatus.CONDITIONAL.value
        elif passed:
            status = RecommendationStatus.APPROVED.value
        elif recommendation.decision_score.overall_score > 0.4:
            status = RecommendationStatus.DEFERRED.value
        else:
            status = RecommendationStatus.REJECTED.value

        return passed and status == RecommendationStatus.APPROVED.value, status, "; ".join(notes) or "Validated."
