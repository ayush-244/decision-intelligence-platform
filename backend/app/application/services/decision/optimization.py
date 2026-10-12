"""Constraint-aware ranking and Pareto-style optimization."""

from __future__ import annotations

from app.application.dto.decision import RecommendationDTO


class OptimizationEngine:
    """Rank intervention plans by decision score with budget and constraint awareness."""

    def rank(
        self,
        candidates: list[RecommendationDTO],
        *,
        max_recommendations: int = 10,
    ) -> tuple[RecommendationDTO, ...]:
        approved = [c for c in candidates if c.validation_passed and c.status != "rejected"]
        approved.sort(key=lambda r: (-r.decision_score.overall_score, r.rank))
        return tuple(approved[:max_recommendations])

    def pareto_dominated(self, a: RecommendationDTO, b: RecommendationDTO) -> bool:
        """True if a is dominated by b on ROI vs risk."""
        return (
            b.decision_score.roi >= a.decision_score.roi
            and b.decision_score.risk >= a.decision_score.risk
            and (
                b.decision_score.roi > a.decision_score.roi
                or b.decision_score.risk > a.decision_score.risk
            )
        )

    def filter_pareto_front(
        self, candidates: list[RecommendationDTO]
    ) -> list[RecommendationDTO]:
        front: list[RecommendationDTO] = []
        for cand in candidates:
            if not any(self.pareto_dominated(cand, other) for other in candidates if other is not cand):
                front.append(cand)
        return front
