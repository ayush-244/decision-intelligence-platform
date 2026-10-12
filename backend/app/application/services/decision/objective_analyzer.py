"""Analyze business objectives and alignment weights."""

from __future__ import annotations

from app.application.dto.decision import DecisionRequestDTO, ObjectiveWeightDTO
from app.domain.value_objects.decision import DecisionObjective


class ObjectiveAnalyzer:
    """Resolve primary and weighted objectives for optimization."""

    DEFAULT_WEIGHTS: dict[str, float] = {
        DecisionObjective.MAXIMIZE_REVENUE.value: 0.35,
        DecisionObjective.MAXIMIZE_PROFIT.value: 0.30,
        DecisionObjective.MINIMIZE_CHURN.value: 0.25,
        DecisionObjective.INCREASE_RETENTION.value: 0.25,
        DecisionObjective.REDUCE_COST.value: 0.20,
        DecisionObjective.IMPROVE_SATISFACTION.value: 0.15,
        DecisionObjective.IMPROVE_CONVERSION.value: 0.20,
    }

    def analyze(self, request: DecisionRequestDTO) -> tuple[str, dict[str, float]]:
        weights: dict[str, float] = dict(self.DEFAULT_WEIGHTS)
        if request.objective_weights:
            for ow in request.objective_weights:
                weights[ow.objective] = ow.weight
        primary = request.primary_objective
        if primary not in weights:
            weights[primary] = 1.0
        total = sum(weights.values()) or 1.0
        normalized = {k: v / total for k, v in weights.items()}
        return primary, normalized

    def alignment_score(
        self,
        *,
        primary_objective: str,
        outcome_delta: float,
        roi: float,
        risk: float,
        weights: dict[str, float],
    ) -> float:
        """Higher when outcome direction matches objective."""
        revenue_objectives = {
            DecisionObjective.MAXIMIZE_REVENUE.value,
            DecisionObjective.MAXIMIZE_PROFIT.value,
            DecisionObjective.IMPROVE_CONVERSION.value,
            DecisionObjective.INCREASE_RETENTION.value,
        }
        cost_objectives = {DecisionObjective.REDUCE_COST.value}
        churn_objectives = {DecisionObjective.MINIMIZE_CHURN.value}

        base = 0.5
        if primary_objective in revenue_objectives:
            base = 0.5 + (0.5 if outcome_delta > 0 else -0.3)
        elif primary_objective in cost_objectives:
            base = 0.5 + (0.5 if outcome_delta < 0 else -0.2)
        elif primary_objective in churn_objectives:
            base = 0.5 + (0.5 if outcome_delta < 0 else -0.3)

        weighted = sum(weights.get(k, 0) for k in weights) * base
        return max(0.0, min(1.0, weighted * 0.6 + min(roi, 1.0) * 0.2 + (1 - risk) * 0.2))
