"""Translate technical outputs into executive business language."""

from __future__ import annotations


class BusinessLanguageEngine:
    """Convert statistical/causal jargon into accurate executive prose."""

    @staticmethod
    def treatment_effect_narrative(
        *,
        treatment: str,
        outcome: str,
        ate: float | None,
        ci_lower: float | None,
        ci_upper: float | None,
        identified: bool,
    ) -> str:
        if ate is None:
            return (
                f"A reliable causal effect of {treatment} on {outcome} could not be estimated "
                "with the available evidence."
            )
        direction = "increase" if ate >= 0 else "decrease"
        pct = abs(ate) * 100 if abs(ate) < 2 else ate
        unit = "%" if abs(ate) < 2 else " units"
        base = (
            f"Changing {treatment} is estimated to {direction} {outcome} by approximately "
            f"{pct:.1f}{unit if abs(ate) < 2 else ''}."
        )
        if ci_lower is not None and ci_upper is not None:
            base += f" The plausible range is {ci_lower:.2g} to {ci_upper:.2g}."
        if not identified:
            base += " This estimate relies on causal assumptions that should be validated before action."
        else:
            base += " This conclusion is supported by the backdoor identification strategy applied in our causal model."
        return base

    @staticmethod
    def simulation_narrative(
        *,
        scenario_name: str,
        baseline: float,
        expected: float,
        probability_improvement: float,
    ) -> str:
        delta = expected - baseline
        direction = "improve" if delta >= 0 else "reduce"
        return (
            f"Under scenario '{scenario_name}', we project outcomes to {direction} by "
            f"{abs(delta):.4g} (from {baseline:.4g} to {expected:.4g}). "
            f"There is a {probability_improvement:.0%} estimated probability of improvement "
            "relative to the status quo, subject to simulation assumptions."
        )

    @staticmethod
    def roi_narrative(roi: float, cost: float, revenue: float) -> str:
        return (
            f"The intervention is projected to deliver {roi:.0%} return on investment, "
            f"with estimated cost of {cost:,.0f} and revenue impact of {revenue:,.0f}. "
            "These figures are illustrative and depend on business assumptions documented in the report."
        )

    @staticmethod
    def confidence_label(score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.5:
            return "moderate"
        return "low"

    @staticmethod
    def executive_summary(
        *,
        objective: str,
        top_recommendation: str | None,
        confidence: str,
        roi: float | None,
    ) -> str:
        if not top_recommendation:
            return (
                f"For the objective '{objective}', no recommendation met our confidence and "
                "risk thresholds. Leadership should review constraints or gather additional evidence."
            )
        roi_text = f" with projected ROI of {roi:.0%}" if roi is not None else ""
        return (
            f"For '{objective}', our top recommendation is: {top_recommendation}{roi_text}. "
            f"Overall confidence in this direction is {confidence}. "
            "Detailed evidence, tradeoffs, and implementation steps follow in this report."
        )
