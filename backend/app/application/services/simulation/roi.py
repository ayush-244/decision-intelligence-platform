"""ROI and cost-benefit estimation for simulated interventions."""

from __future__ import annotations

from typing import Any

from app.application.dto.simulation import CounterfactualOutcomeDTO, ROIEstimateDTO


class ROICalculator:
    """Translate counterfactual outcome deltas into business ROI metrics."""

    def calculate(
        self,
        *,
        counterfactual: CounterfactualOutcomeDTO,
        roi_assumptions: dict[str, Any],
    ) -> ROIEstimateDTO:
        unit_value = float(roi_assumptions.get("revenue_per_outcome_unit", 1.0))
        intervention_cost = float(roi_assumptions.get("intervention_cost", 0.0))
        fixed_cost = float(roi_assumptions.get("fixed_cost", 0.0))
        savings_per_unit = float(roi_assumptions.get("savings_per_outcome_unit", 0.0))

        outcome_delta = counterfactual.expected_outcome - counterfactual.baseline_outcome
        expected_revenue = outcome_delta * unit_value
        expected_savings = max(0.0, outcome_delta * savings_per_unit)
        expected_cost = intervention_cost + fixed_cost
        net_benefit = expected_revenue + expected_savings - expected_cost
        expected_roi = net_benefit / expected_cost if expected_cost > 0 else 0.0
        cbr = (expected_revenue + expected_savings) / expected_cost if expected_cost > 0 else 0.0
        payback = (expected_cost / (expected_revenue + expected_savings)) if (expected_revenue + expected_savings) > 0 else None

        assumptions = (
            f"Revenue per outcome unit: {unit_value}",
            f"Intervention cost: {intervention_cost}",
            f"Fixed cost: {fixed_cost}",
            f"Savings per outcome unit: {savings_per_unit}",
            "ROI is illustrative — not a guarantee of financial performance.",
        )
        return ROIEstimateDTO(
            expected_cost=round(expected_cost, 4),
            expected_revenue=round(expected_revenue, 4),
            expected_savings=round(expected_savings, 4),
            expected_roi=round(expected_roi, 4),
            payback_period=round(payback, 4) if payback is not None else None,
            cost_benefit_ratio=round(cbr, 4),
            assumptions=assumptions,
        )

    @staticmethod
    def calculate_from_payload(
        *,
        counterfactual_data: dict[str, Any],
        roi_assumptions: dict[str, Any],
    ) -> ROIEstimateDTO:
        from app.application.dto.simulation import CounterfactualOutcomeDTO

        cf = CounterfactualOutcomeDTO(
            baseline_outcome=counterfactual_data.get("baseline_outcome", 0),
            expected_outcome=counterfactual_data.get("expected_outcome", 0),
            expected_treatment_effect=counterfactual_data.get("expected_treatment_effect", 0),
            ci_lower=counterfactual_data.get("ci_lower", 0),
            ci_upper=counterfactual_data.get("ci_upper", 0),
            probability_improvement=counterfactual_data.get("probability_improvement", 0.5),
            probability_deterioration=counterfactual_data.get("probability_deterioration", 0.5),
            uncertainty_score=counterfactual_data.get("uncertainty_score", 0.5),
            extrapolation_warnings=tuple(counterfactual_data.get("extrapolation_warnings", [])),
        )
        return ROICalculator().calculate(counterfactual=cf, roi_assumptions=roi_assumptions)
