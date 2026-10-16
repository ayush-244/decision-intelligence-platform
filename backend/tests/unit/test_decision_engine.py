"""Unit tests for decision intelligence engine."""

from __future__ import annotations

from app.application.dto.decision import DecisionConstraintDTO
from app.application.services.decision.constraint_manager import ConstraintManager
from app.application.services.decision.objective_analyzer import ObjectiveAnalyzer
from app.application.services.decision.optimization import OptimizationEngine
from app.application.services.decision.scoring import DecisionScorer
from app.domain.entities.simulation_run import SimulationRun
from app.domain.value_objects.simulation import SimulationRunStatus
from uuid import uuid4
from app.shared.utils.datetime import utc_now


def _simulation_run(roi: float, risk: float, uncertainty: float, delta: float) -> SimulationRun:
    now = utc_now()
    return SimulationRun(
        id=uuid4(),
        dataset_id=uuid4(),
        version_id=uuid4(),
        organization_id=uuid4(),
        project_id=uuid4(),
        causal_analysis_id=uuid4(),
        statistical_analysis_id=None,
        scenario_id=uuid4(),
        created_by=uuid4(),
        status=SimulationRunStatus.COMPLETED,
        name="Test scenario",
        configuration={},
        result={
            "roi": {"expected_roi": roi, "expected_cost": 100},
            "risk": {"overall_score": risk},
            "counterfactual": {
                "baseline_outcome": 10.0,
                "expected_outcome": 10.0 + delta,
                "uncertainty_score": uncertainty,
            },
        },
        error_message=None,
        executed_at=now,
        created_at=now,
        updated_at=now,
    )


def test_decision_scorer_high_impact() -> None:
    score = DecisionScorer().score(
        outcome_delta=5.0,
        max_delta=5.0,
        roi=0.5,
        confidence=0.8,
        risk=0.2,
        feasibility=0.9,
        strategic_alignment=0.85,
        constraint_satisfaction=1.0,
    )
    assert score.overall_score > 0.6
    assert score.business_impact == 1.0


def test_constraint_manager_budget() -> None:
    sim = _simulation_run(roi=0.3, risk=0.3, uncertainty=0.2, delta=2.0)
    evals, ok, sat = ConstraintManager().evaluate(
        constraints=(),
        simulation=sim,
        risk_tolerance=0.7,
        min_confidence=0.5,
        max_budget=50.0,
    )
    assert not ok
    assert sat < 1.0
    assert any(e["type"] == "max_budget" for e in evals)


def test_objective_analyzer_alignment() -> None:
    analyzer = ObjectiveAnalyzer()
    score = analyzer.alignment_score(
        primary_objective="maximize_revenue",
        outcome_delta=3.0,
        roi=0.4,
        risk=0.2,
        weights={"maximize_revenue": 1.0},
    )
    assert score > 0.5


def test_optimization_ranking() -> None:
    from app.application.dto.decision import DecisionScoreDTO, EvidenceChainDTO, RecommendationDTO

    def rec(score: float, rank: int) -> RecommendationDTO:
        ds = DecisionScoreDTO(0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1.0, score, "test")
        ev = EvidenceChainDTO(None, "c", "s", "sc", None, "c", "s")
        return RecommendationDTO(
            rank=rank, status="approved", title=f"R{rank}", summary="", reason="",
            evidence=ev, expected_outcome=10, confidence=0.8, roi=0.2, risk=0.3,
            required_assumptions=(), implementation_difficulty="low",
            expected_timeline="1m", dependencies=(), alternative_options=(),
            business_explanation="", recommended_order=rank, decision_score=ds,
            validation_passed=True, validation_notes=(),
        )

    ranked = OptimizationEngine().rank([rec(0.6, 1), rec(0.9, 2), rec(0.4, 3)])
    assert ranked[0].decision_score.overall_score == 0.9
