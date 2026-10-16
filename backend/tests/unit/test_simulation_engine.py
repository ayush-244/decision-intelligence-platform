"""Unit tests for simulation engine components."""

from __future__ import annotations

import polars as pl

from app.application.dto.causal import TreatmentEffectDTO
from app.application.dto.simulation import ConstraintDTO, InterventionDTO
from app.application.services.simulation.constraints import ConstraintEngine
from app.application.services.simulation.counterfactual import CounterfactualGenerator
from app.application.services.simulation.intervention_validator import InterventionValidator
from app.application.services.simulation.monte_carlo import MonteCarloEngine
from app.application.services.simulation.roi import ROICalculator
from app.domain.value_objects.causal import CausalEstimatorType


def test_intervention_validator_rejects_missing_variable() -> None:
    frame = pl.DataFrame({"treatment": [0, 1], "outcome": [10.0, 15.0]})
    result = InterventionValidator().validate(
        frame=frame,
        interventions=(InterventionDTO(variable="marketing", mode="relative", value=0.2),),
        treatment="treatment",
    )
    assert not result.valid
    assert any("not found" in e for e in result.errors)


def test_counterfactual_positive_effect() -> None:
    frame = pl.DataFrame({"treatment": [0, 0, 1, 1], "outcome": [10.0, 11.0, 15.0, 16.0]})
    te = TreatmentEffectDTO(
        estimator=CausalEstimatorType.DIFFERENCE_IN_MEANS,
        ate=5.0,
        att=5.0,
        atc=5.0,
        std_error=1.0,
        confidence_level=0.95,
        ci_lower=3.0,
        ci_upper=7.0,
        p_value=0.01,
        details={},
    )
    cf = CounterfactualGenerator().generate(
        frame=frame,
        treatment="treatment",
        outcome="outcome",
        treatment_effect=te,
        interventions=(InterventionDTO(variable="treatment", mode="relative", value=0.2),),
        confidence_level=0.95,
    )
    assert cf.expected_outcome > cf.baseline_outcome
    assert cf.expected_treatment_effect > 0


def test_monte_carlo_produces_distribution() -> None:
    from app.application.dto.simulation import CounterfactualOutcomeDTO

    cf = CounterfactualOutcomeDTO(
        baseline_outcome=10.0,
        expected_outcome=12.0,
        expected_treatment_effect=2.0,
        ci_lower=10.5,
        ci_upper=13.5,
        probability_improvement=0.8,
        probability_deterioration=0.2,
        uncertainty_score=0.3,
        extrapolation_warnings=(),
    )
    mc = MonteCarloEngine().simulate(counterfactual=cf, std_error=0.5, iterations=500)
    assert mc.iterations == 500
    assert len(mc.distribution) == 200
    assert mc.p05 <= mc.median <= mc.p95


def test_roi_calculator() -> None:
    from app.application.dto.simulation import CounterfactualOutcomeDTO

    cf = CounterfactualOutcomeDTO(
        baseline_outcome=100.0,
        expected_outcome=120.0,
        expected_treatment_effect=20.0,
        ci_lower=110.0,
        ci_upper=130.0,
        probability_improvement=0.9,
        probability_deterioration=0.1,
        uncertainty_score=0.2,
        extrapolation_warnings=(),
    )
    roi = ROICalculator().calculate(
        counterfactual=cf,
        roi_assumptions={"revenue_per_outcome_unit": 10, "intervention_cost": 50},
    )
    assert roi.expected_revenue == 200.0
    assert roi.expected_roi > 0


def test_constraint_budget_violation() -> None:
    from app.application.dto.simulation import CounterfactualOutcomeDTO, ROIEstimateDTO

    cf = CounterfactualOutcomeDTO(
        baseline_outcome=10.0,
        expected_outcome=12.0,
        expected_treatment_effect=2.0,
        ci_lower=10.0,
        ci_upper=14.0,
        probability_improvement=0.7,
        probability_deterioration=0.3,
        uncertainty_score=0.3,
        extrapolation_warnings=(),
    )
    roi = ROIEstimateDTO(1000.0, 200.0, 0.0, 0.1, None, 0.2, ())
    result = ConstraintEngine().evaluate(
        constraints=(
            ConstraintDTO(
                type="max_budget",
                severity="hard",
                threshold=500.0,
                description="Max spend",
            ),
        ),
        counterfactual=cf,
        roi=roi,
    )
    assert len(result) == 1
    assert not result[0].satisfied
