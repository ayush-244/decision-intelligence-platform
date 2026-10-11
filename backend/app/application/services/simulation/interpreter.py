"""Business interpretation of simulation results."""

from __future__ import annotations

from app.application.dto.simulation import (
    CounterfactualOutcomeDTO,
    RiskAssessmentDTO,
    ROIEstimateDTO,
    ScenarioComparisonDTO,
    SimulationInterpretationDTO,
)


class SimulationInterpreter:
    """Translate simulation outputs into actionable business language."""

    def interpret(
        self,
        *,
        objective: str,
        scenario_name: str,
        counterfactual: CounterfactualOutcomeDTO,
        risk: RiskAssessmentDTO,
        roi: ROIEstimateDTO,
        comparison: tuple[ScenarioComparisonDTO, ...],
        extrapolation_warnings: tuple[str, ...],
    ) -> SimulationInterpretationDTO:
        delta = counterfactual.expected_outcome - counterfactual.baseline_outcome
        direction = "increase" if delta >= 0 else "decrease"
        limitations: list[str] = [
            "Simulation estimates consequences under causal assumptions — not forecasts.",
            "Results depend on the quality of the underlying causal model.",
            risk.summary,
        ]
        limitations.extend(extrapolation_warnings)
        limitations.extend(counterfactual.extrapolation_warnings)

        business = (
            f"Scenario '{scenario_name}' is projected to {direction} the outcome by "
            f"{abs(delta):.4g} (from {counterfactual.baseline_outcome:.4g} to "
            f"{counterfactual.expected_outcome:.4g}). "
            f"Probability of improvement: {counterfactual.probability_improvement:.0%}. "
            f"Expected ROI: {roi.expected_roi:.1%} with overall risk score {risk.overall_score:.0%}."
        )

        actions: list[str] = []
        if risk.overall_score >= 0.65:
            actions.append("Consider pilot testing before full rollout due to elevated risk.")
        if counterfactual.extrapolation_warnings:
            actions.append("Collect data closer to proposed intervention levels before committing.")
        if comparison:
            best = min(comparison, key=lambda c: c.rank)
            actions.append(f"Highest-ranked scenario: {best.scenario_name} (rank {best.rank}).")
        if not actions:
            actions.append("Review assumptions with stakeholders and validate with A/B test if feasible.")

        alts = tuple(c.scenario_name for c in sorted(comparison, key=lambda x: x.rank))

        return SimulationInterpretationDTO(
            scenario_summary=f"Objective: {objective}",
            business_interpretation=business,
            limitations=tuple(limitations),
            recommended_actions=tuple(actions),
            alternative_scenarios=alts,
        )
