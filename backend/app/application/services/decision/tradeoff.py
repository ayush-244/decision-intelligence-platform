"""Tradeoff analysis between ranked recommendations."""

from __future__ import annotations

from app.application.dto.decision import RecommendationDTO, TradeoffDTO


class TradeoffEngine:
    """Explain pairwise tradeoffs between top recommendations."""

    def analyze(self, ranked: tuple[RecommendationDTO, ...]) -> tuple[TradeoffDTO, ...]:
        if len(ranked) < 2:
            return ()
        tradeoffs: list[TradeoffDTO] = []
        top = ranked[0]
        for alt in ranked[1:3]:
            if alt.decision_score.roi > top.decision_score.roi and alt.risk > top.risk:
                tradeoffs.append(TradeoffDTO(
                    dimension_a="ROI",
                    dimension_b="Risk",
                    option_a=top.title,
                    option_b=alt.title,
                    tradeoff_summary=(
                        f"{alt.title} offers higher ROI ({alt.roi:.1%}) but elevated risk "
                        f"({alt.risk:.0%}) vs {top.title} ({top.roi:.1%} ROI, {top.risk:.0%} risk)."
                    ),
                    recommendation=(
                        f"Choose {top.title} if risk tolerance is limited; "
                        f"consider {alt.title} if upside justifies exposure."
                    ),
                ))
            if alt.roi < top.roi and alt.risk < top.risk:
                tradeoffs.append(TradeoffDTO(
                    dimension_a="Cost / Risk",
                    dimension_b="Revenue",
                    option_a=alt.title,
                    option_b=top.title,
                    tradeoff_summary=(
                        f"{alt.title} is lower risk ({alt.risk:.0%}) but lower ROI ({alt.roi:.1%}) "
                        f"than {top.title}."
                    ),
                    recommendation=f"{alt.title} suits conservative rollout; {top.title} for growth priority.",
                ))
            if alt.confidence > top.confidence and alt.decision_score.overall_score < top.decision_score.overall_score:
                tradeoffs.append(TradeoffDTO(
                    dimension_a="Confidence",
                    dimension_b="Business Impact",
                    option_a=alt.title,
                    option_b=top.title,
                    tradeoff_summary=(
                        f"{alt.title} has higher statistical confidence ({alt.confidence:.0%}) "
                        f"but lower composite score."
                    ),
                    recommendation="Higher confidence does not always imply higher expected value.",
                ))
        return tuple(tradeoffs)
