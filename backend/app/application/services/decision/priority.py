"""Priority scoring for implementation ordering."""

from __future__ import annotations

from app.application.dto.decision import PriorityDTO, RecommendationDTO


class PriorityEngine:
    """Rank recommendations by implementation priority."""

    FACTOR_WEIGHTS = {
        "business_value": 0.25,
        "roi": 0.20,
        "risk_inverse": 0.15,
        "confidence": 0.15,
        "feasibility": 0.10,
        "causal_reliability": 0.15,
    }

    def prioritize(
        self, recommendations: tuple[RecommendationDTO, ...]
    ) -> tuple[PriorityDTO, ...]:
        scored: list[tuple[float, RecommendationDTO, list[tuple[str, float, str]]]] = []
        for rec in recommendations:
            factors = [
                ("Business value", rec.decision_score.business_impact, "Expected outcome impact"),
                ("ROI", rec.decision_score.roi, "Return on intervention investment"),
                ("Low risk", rec.decision_score.risk, "Inverse risk contribution"),
                ("Confidence", rec.decision_score.confidence, "Statistical + causal certainty"),
                ("Feasibility", rec.decision_score.feasibility, "Constraint and implementation fit"),
                ("Alignment", rec.decision_score.strategic_alignment, "Objective alignment"),
            ]
            priority = sum(
                score * self.FACTOR_WEIGHTS.get(
                    {"Business value": "business_value", "ROI": "roi", "Low risk": "risk_inverse",
                     "Confidence": "confidence", "Feasibility": "feasibility",
                     "Alignment": "causal_reliability"}.get(name, "business_value"),
                    0.1,
                )
                for name, score, _ in factors
            )
            scored.append((priority, rec, factors))

        scored.sort(key=lambda x: -x[0])
        return tuple(
            PriorityDTO(
                simulation_run_id=rec.evidence.simulation_run_id,
                title=rec.title,
                priority_score=round(score, 4),
                rank=idx + 1,
                factors=tuple((n, round(s, 3), e) for n, s, e in factors),
            )
            for idx, (score, rec, factors) in enumerate(scored)
        )
