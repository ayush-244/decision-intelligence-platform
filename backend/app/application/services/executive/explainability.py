"""Explainability blocks with full evidence chains."""

from __future__ import annotations

from typing import Any

from app.application.dto.executive import EvidenceChainNarrativeDTO, ExplainabilityBlockDTO
from app.application.services.executive.business_language import BusinessLanguageEngine
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.decision_run import DecisionRun
from app.domain.entities.simulation_run import SimulationRun
from app.domain.value_objects.executive import ConfidenceLevel


class ExplainabilityEngine:
    """Build transparent evidence chains for each recommendation."""

    def __init__(self) -> None:
        self._language = BusinessLanguageEngine()

    def explain_recommendation(
        self,
        *,
        rec: dict[str, Any],
        causal: CausalAnalysisRun | None,
        simulation: SimulationRun | None,
        decision: DecisionRun,
    ) -> ExplainabilityBlockDTO:
        te = (causal.result.get("treatment_effect", {}) if causal else {}) or {}
        id_report = (causal.result.get("identification", {}) if causal else {}) or {}
        sim_result = simulation.result if simulation else {}
        cf = sim_result.get("counterfactual", {})

        statistical = None
        if te.get("p_value") is not None:
            statistical = (
                f"Statistical test indicates a treatment effect with p-value {te.get('p_value'):.4g}. "
                f"Effect size (ATE): {te.get('ate', 'N/A')}."
            )

        causal_text = self._language.treatment_effect_narrative(
            treatment=causal.treatment if causal else "treatment",
            outcome=causal.outcome if causal else "outcome",
            ate=te.get("ate"),
            ci_lower=te.get("ci_lower"),
            ci_upper=te.get("ci_upper"),
            identified=bool(id_report.get("identified", False)),
        )

        sim_text = "Simulation evidence not linked."
        if simulation and cf:
            sim_text = self._language.simulation_narrative(
                scenario_name=simulation.name,
                baseline=float(cf.get("baseline_outcome", 0)),
                expected=float(cf.get("expected_outcome", 0)),
                probability_improvement=float(cf.get("probability_improvement", 0.5)),
            )

        decision_text = decision.result.get("overall_summary", "Decision analysis completed.")

        confidence_score = float(rec.get("confidence", 0.5))
        level = self._language.confidence_label(confidence_score)

        evidence = EvidenceChainNarrativeDTO(
            statistical=statistical,
            causal=causal_text,
            simulation=sim_text,
            decision=decision_text,
            confidence_level=level,
            confidence_score=round(confidence_score, 3),
        )

        assumptions = tuple(rec.get("required_assumptions", [])[:5])
        limitations = tuple(decision.result.get("limitations", [])[:3])
        alts = tuple(rec.get("alternative_options", [])[:3]) or (
            "Maintain status quo and monitor KPIs.",
            "Run a controlled pilot before full rollout.",
        )

        why = (
            f"This recommendation ranks #{rec.get('rank')} because it scores "
            f"{rec.get('decision_score', {}).get('overall_score', 0):.2f} on our composite index, "
            f"balancing impact, ROI, confidence, and risk."
        )

        return ExplainabilityBlockDTO(
            recommendation_title=str(rec.get("title", "Recommendation")),
            why=why,
            evidence=evidence,
            assumptions=assumptions,
            limitations=limitations,
            business_interpretation=str(rec.get("business_explanation", "")),
            alternative_actions=alts,
        )

    def aggregate_confidence(self, blocks: tuple[ExplainabilityBlockDTO, ...]) -> dict[str, Any]:
        if not blocks:
            return {"level": ConfidenceLevel.LOW.value, "score": 0.0, "summary": "Insufficient evidence."}
        avg = sum(b.evidence.confidence_score for b in blocks) / len(blocks)
        level = self._language.confidence_label(avg)
        return {
            "level": level,
            "score": round(avg, 3),
            "summary": (
                f"Overall confidence is {level} ({avg:.0%}) based on the evidence chain "
                "from statistics through causal modeling, simulation, and decision scoring."
            ),
        }
