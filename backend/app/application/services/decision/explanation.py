"""Business explanations for decision outputs."""

from __future__ import annotations

from app.application.dto.decision import DecisionResultDTO, RecommendationDTO


class ExplanationEngine:
    """Synthesize executive-level decision narratives."""

    def summarize(
        self,
        *,
        primary_objective: str,
        recommendations: tuple[RecommendationDTO, ...],
        rejected_count: int,
    ) -> tuple[str, str | None, tuple[str, ...]]:
        if not recommendations:
            return (
                "No recommendations met validation thresholds. Review constraints or gather more evidence.",
                None,
                ("Lower min_confidence or risk_tolerance only with explicit stakeholder acceptance.",),
            )

        best = recommendations[0]
        summary = (
            f"For objective '{primary_objective}', '{best.title}' ranks first with composite score "
            f"{best.decision_score.overall_score:.2f}. Expected outcome {best.expected_outcome:.4g} "
            f"at {best.confidence:.0%} confidence, ROI {best.roi:.1%}, risk {best.risk:.0%}. "
            f"{rejected_count} option(s) rejected for insufficient evidence."
        )
        deferred = tuple(
            r.title for r in recommendations if r.status == "deferred"
        )
        limitations = (
            "Recommendations chain statistical → causal → simulation evidence.",
            "Rejected options lack sufficient confidence or violate constraints.",
            "Implementation order should follow priority ranks unless tradeoffs dictate otherwise.",
        )
        return summary, best.title, limitations

    def enrich_result_summary(self, result: DecisionResultDTO) -> str:
        return result.overall_summary
