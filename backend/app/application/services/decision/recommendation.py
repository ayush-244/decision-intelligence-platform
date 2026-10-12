"""Generate structured recommendations from simulation evidence."""

from __future__ import annotations

from app.application.dto.decision import (
    DecisionScoreDTO,
    EvidenceChainDTO,
    RecommendationDTO,
)
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.simulation_run import SimulationRun
from app.domain.value_objects.decision import RecommendationStatus


class RecommendationGenerator:
    """Build recommendation artifacts from completed simulation runs."""

    def build(
        self,
        *,
        simulation: SimulationRun,
        causal: CausalAnalysisRun,
        rank: int,
        decision_score: DecisionScoreDTO,
        status: str,
        validation_passed: bool,
        validation_notes: str,
        strategic_alignment: float,
    ) -> RecommendationDTO:
        result = simulation.result or {}
        cf = result.get("counterfactual", {})
        roi_data = result.get("roi", {})
        risk_data = result.get("risk", {})
        interp = result.get("interpretation", {})

        baseline = float(cf.get("baseline_outcome", 0))
        expected = float(cf.get("expected_outcome", baseline))
        outcome_delta = expected - baseline
        confidence = 1.0 - float(cf.get("uncertainty_score", 0.5))
        roi = float(roi_data.get("expected_roi", 0))
        risk = float(risk_data.get("overall_score", 0.5))

        causal_id = causal.result.get("identification", {})
        identified = bool(causal_id.get("identified", False))
        causal_summary = causal_id.get("reasoning", "Causal model applied.")[:200]

        te = causal.result.get("treatment_effect", {})
        statistical_summary = None
        if te.get("p_value") is not None:
            statistical_summary = f"Treatment effect p-value: {te.get('p_value')}"

        evidence = EvidenceChainDTO(
            statistical_analysis_id=(
                str(simulation.statistical_analysis_id)
                if simulation.statistical_analysis_id
                else None
            ),
            causal_analysis_id=str(simulation.causal_analysis_id),
            simulation_run_id=str(simulation.id),
            scenario_id=str(simulation.scenario_id),
            statistical_summary=statistical_summary,
            causal_summary=causal_summary,
            simulation_summary=interp.get("business_interpretation", simulation.name)[:200],
        )

        difficulty = "low" if risk < 0.35 else "moderate" if risk < 0.65 else "high"
        timeline = "1-3 months" if difficulty == "low" else "3-6 months" if difficulty == "moderate" else "6+ months"

        assumptions = tuple(result.get("assumptions", [])[:5])
        limitations = tuple(interp.get("limitations", [])[:3])

        title = f"Implement: {simulation.name}"
        summary = (
            f"Projected outcome change {outcome_delta:+.4g} with ROI {roi:.1%} "
            f"and risk {risk:.0%} (score {decision_score.overall_score:.2f})."
        )
        reason = (
            f"Ranked #{rank} based on weighted evidence: statistical support, "
            f"causal identification ({'yes' if identified else 'partial'}), "
            f"simulation counterfactual, and constraint fit."
        )

        return RecommendationDTO(
            rank=rank,
            status=status if validation_passed else (
                RecommendationStatus.REJECTED.value
                if status == RecommendationStatus.REJECTED.value
                else status
            ),
            title=title,
            summary=summary,
            reason=reason,
            evidence=evidence,
            expected_outcome=expected,
            confidence=round(confidence, 4),
            roi=round(roi, 4),
            risk=round(risk, 4),
            required_assumptions=assumptions,
            implementation_difficulty=difficulty,
            expected_timeline=timeline,
            dependencies=(f"Causal analysis {simulation.causal_analysis_id}",),
            alternative_options=tuple(interp.get("alternative_scenarios", [])[:3]),
            business_explanation=interp.get("business_interpretation", summary),
            recommended_order=rank,
            decision_score=decision_score,
            validation_passed=validation_passed,
            validation_notes=(validation_notes, *limitations),
        )
