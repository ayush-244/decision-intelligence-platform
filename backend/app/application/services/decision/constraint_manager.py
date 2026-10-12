"""Decision-level constraint management."""

from __future__ import annotations

from app.application.dto.decision import DecisionConstraintDTO
from app.domain.entities.simulation_run import SimulationRun


class ConstraintManager:
    """Evaluate decision constraints against simulation evidence."""

    def evaluate(
        self,
        *,
        constraints: tuple[DecisionConstraintDTO, ...],
        simulation: SimulationRun,
        risk_tolerance: float,
        min_confidence: float,
        max_budget: float | None,
    ) -> tuple[dict[str, object], bool, float]:
        result = simulation.result or {}
        roi = float(result.get("roi", {}).get("expected_roi", 0))
        risk = float(result.get("risk", {}).get("overall_score", 1))
        cf = result.get("counterfactual", {})
        confidence = 1.0 - float(cf.get("uncertainty_score", 0.5))
        cost = float(result.get("roi", {}).get("expected_cost", 0))

        evaluations: list[dict[str, object]] = []
        all_satisfied = True
        satisfaction = 1.0

        if max_budget is not None:
            ok = cost <= max_budget
            evaluations.append({
                "type": "max_budget",
                "satisfied": ok,
                "actual": cost,
                "threshold": max_budget,
                "message": f"Cost {cost:.2f} vs budget {max_budget:.2f}",
            })
            if not ok:
                all_satisfied = False
                satisfaction -= 0.25

        ok = risk <= risk_tolerance
        evaluations.append({
            "type": "max_risk",
            "satisfied": ok,
            "actual": risk,
            "threshold": risk_tolerance,
            "message": f"Risk {risk:.0%} vs tolerance {risk_tolerance:.0%}",
        })
        if not ok:
            all_satisfied = False
            satisfaction -= 0.2

        ok = confidence >= min_confidence
        evaluations.append({
            "type": "min_confidence",
            "satisfied": ok,
            "actual": confidence,
            "threshold": min_confidence,
            "message": f"Confidence {confidence:.0%} vs minimum {min_confidence:.0%}",
        })
        if not ok:
            all_satisfied = False
            satisfaction -= 0.2

        for constraint in constraints:
            ctype = constraint.type
            threshold = constraint.threshold
            if ctype == "min_roi" and threshold is not None:
                ok = roi >= threshold
                evaluations.append({
                    "type": ctype,
                    "satisfied": ok,
                    "actual": roi,
                    "threshold": threshold,
                    "message": constraint.description or f"ROI {roi:.1%} vs min {threshold:.1%}",
                })
                if not ok:
                    all_satisfied = False
                    satisfaction -= 0.15
            elif ctype == "max_budget" and threshold is not None:
                ok = cost <= threshold
                evaluations.append({
                    "type": ctype,
                    "satisfied": ok,
                    "severity": constraint.severity,
                    "actual": cost,
                    "threshold": threshold,
                    "message": constraint.description,
                })
                if not ok and constraint.severity == "hard":
                    all_satisfied = False
                    satisfaction -= 0.2

        satisfaction = max(0.0, min(1.0, satisfaction))
        return tuple(evaluations), all_satisfied, satisfaction
