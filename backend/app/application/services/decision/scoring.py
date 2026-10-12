"""Explainable decision scoring methodology."""

from __future__ import annotations

from app.application.dto.decision import DecisionScoreDTO


class DecisionScorer:
    """Compute weighted recommendation scores from evidence components."""

    METHODOLOGY = (
        "Weighted composite: business_impact (25%), ROI (20%), confidence (20%), "
        "risk_inverse (15%), feasibility (10%), strategic_alignment (10%). "
        "All inputs normalized to [0,1] from simulation and causal evidence."
    )

    WEIGHTS = {
        "business_impact": 0.25,
        "roi": 0.20,
        "confidence": 0.20,
        "risk": 0.15,
        "feasibility": 0.10,
        "strategic_alignment": 0.10,
    }

    def score(
        self,
        *,
        outcome_delta: float,
        max_delta: float,
        roi: float,
        confidence: float,
        risk: float,
        feasibility: float,
        strategic_alignment: float,
        constraint_satisfaction: float,
    ) -> DecisionScoreDTO:
        impact = min(1.0, abs(outcome_delta) / max(max_delta, 1e-6))
        roi_norm = max(0.0, min(1.0, (roi + 1) / 2))
        conf = max(0.0, min(1.0, confidence))
        risk_inv = max(0.0, min(1.0, 1.0 - risk))
        feas = max(0.0, min(1.0, feasibility))
        align = max(0.0, min(1.0, strategic_alignment))
        constraint_sat = max(0.0, min(1.0, constraint_satisfaction))

        overall = (
            impact * self.WEIGHTS["business_impact"]
            + roi_norm * self.WEIGHTS["roi"]
            + conf * self.WEIGHTS["confidence"]
            + risk_inv * self.WEIGHTS["risk"]
            + feas * self.WEIGHTS["feasibility"]
            + align * self.WEIGHTS["strategic_alignment"]
        )
        overall *= constraint_sat

        return DecisionScoreDTO(
            business_impact=round(impact, 4),
            roi=round(roi_norm, 4),
            confidence=round(conf, 4),
            risk=round(risk_inv, 4),
            feasibility=round(feas, 4),
            strategic_alignment=round(align, 4),
            constraint_satisfaction=round(constraint_sat, 4),
            overall_score=round(overall, 4),
            methodology=self.METHODOLOGY,
        )
