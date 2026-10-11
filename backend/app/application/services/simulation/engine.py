"""Simulation Engine — orchestrates counterfactual scenario simulation."""

from __future__ import annotations

from uuid import UUID, uuid4

import polars as pl

from app.application.dto.simulation import (
    ConstraintDTO,
    InterventionDTO,
    SimulationRequestDTO,
    SimulationResultDTO,
)
from app.application.services.intelligence.frame_loader import DatasetFrameLoader
from app.application.services.simulation.comparator import ScenarioComparator
from app.application.services.simulation.constraints import ConstraintEngine
from app.application.services.simulation.counterfactual import CounterfactualGenerator
from app.application.services.simulation.interpreter import SimulationInterpreter
from app.application.services.simulation.intervention_validator import InterventionValidator
from app.application.services.simulation.monte_carlo import MonteCarloEngine
from app.application.services.simulation.roi import ROICalculator
from app.application.services.simulation.risk import RiskEngine
from app.application.services.simulation.serialization import to_jsonable
from app.application.services.simulation.treatment_integrator import TreatmentEffectIntegrator
from app.core.config import Settings
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.simulation_run import SimulationRun
from app.domain.entities.simulation_scenario import SimulationScenario
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.simulation_scenario_repository import SimulationScenarioRepository
from app.domain.value_objects.simulation import SimulationRunStatus
from app.shared.exceptions import BusinessValidationError
from app.shared.utils.datetime import utc_now


class SimulationEngine:
    """Estimate consequences of hypothetical interventions using causal models."""

    def __init__(
        self,
        settings: Settings,
        frame_loader: DatasetFrameLoader,
        runs: SimulationRunRepository,
        scenarios: SimulationScenarioRepository,
        causal_analyses: CausalAnalysisRepository,
    ) -> None:
        self._settings = settings
        self._frame_loader = frame_loader
        self._runs = runs
        self._scenarios = scenarios
        self._causal_analyses = causal_analyses
        self._validator = InterventionValidator()
        self._integrator = TreatmentEffectIntegrator()
        self._counterfactual = CounterfactualGenerator()
        self._monte_carlo = MonteCarloEngine()
        self._constraints = ConstraintEngine()
        self._risk = RiskEngine()
        self._roi = ROICalculator()
        self._interpreter = SimulationInterpreter()
        self._comparator = ScenarioComparator()

    async def simulate(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
        causal_run: CausalAnalysisRun,
        scenario: SimulationScenario,
        request: SimulationRequestDTO,
        created_by: UUID,
        statistical_analysis_id: UUID | None = None,
    ) -> SimulationRun:
        now = utc_now()
        config = to_jsonable(request)
        pending = SimulationRun(
            id=uuid4(),
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            causal_analysis_id=causal_run.id,
            statistical_analysis_id=statistical_analysis_id,
            scenario_id=scenario.id,
            created_by=created_by,
            status=SimulationRunStatus.RUNNING,
            name=request.name,
            configuration=config,
            result={},
            error_message=None,
            executed_at=None,
            created_at=now,
            updated_at=now,
        )
        await self._runs.create(pending)

        try:
            sampled = await self._frame_loader.load(version=version)
            result_dto = self._run_pipeline(
                frame=sampled.frame,
                causal_run=causal_run,
                scenario=scenario,
                request=request,
            )
            result_dict = to_jsonable(result_dto)
            completed = SimulationRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                causal_analysis_id=causal_run.id,
                statistical_analysis_id=statistical_analysis_id,
                scenario_id=scenario.id,
                created_by=created_by,
                status=SimulationRunStatus.COMPLETED,
                name=request.name,
                configuration=config,
                result=result_dict,
                error_message=None,
                executed_at=utc_now(),
                created_at=now,
                updated_at=now,
            )
            return await self._runs.update(completed)
        except Exception as exc:  # noqa: BLE001
            failed = SimulationRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                causal_analysis_id=causal_run.id,
                statistical_analysis_id=statistical_analysis_id,
                scenario_id=scenario.id,
                created_by=created_by,
                status=SimulationRunStatus.FAILED,
                name=request.name,
                configuration=config,
                result={},
                error_message=str(exc),
                executed_at=None,
                created_at=now,
                updated_at=now,
            )
            await self._runs.update(failed)
            raise

    def _run_pipeline(
        self,
        *,
        frame: pl.DataFrame,
        causal_run: CausalAnalysisRun,
        scenario: SimulationScenario,
        request: SimulationRequestDTO,
    ) -> SimulationResultDTO:
        treatment = causal_run.treatment
        outcome = causal_run.outcome
        interventions = request.interventions or self._interventions_from_scenario(scenario)
        constraints = request.constraints or self._constraints_from_scenario(scenario)

        validation = self._validator.validate(
            frame=frame, interventions=interventions, treatment=treatment
        )
        if not validation.valid:
            raise BusinessValidationError(
                "; ".join(validation.errors), code="invalid_interventions"
            )

        treatment_effect = self._integrator.extract(causal_run)
        causal_assumptions = self._integrator.causal_assumptions(causal_run)

        counterfactual = self._counterfactual.generate(
            frame=frame,
            treatment=treatment,
            outcome=outcome,
            treatment_effect=treatment_effect,
            interventions=interventions,
            confidence_level=request.confidence_level,
        )
        if validation.warnings:
            counterfactual = type(counterfactual)(
                baseline_outcome=counterfactual.baseline_outcome,
                expected_outcome=counterfactual.expected_outcome,
                expected_treatment_effect=counterfactual.expected_treatment_effect,
                ci_lower=counterfactual.ci_lower,
                ci_upper=counterfactual.ci_upper,
                probability_improvement=counterfactual.probability_improvement,
                probability_deterioration=counterfactual.probability_deterioration,
                uncertainty_score=counterfactual.uncertainty_score,
                extrapolation_warnings=counterfactual.extrapolation_warnings + validation.warnings,
            )

        std_error = treatment_effect.std_error or abs(counterfactual.expected_treatment_effect) * 0.2
        monte_carlo = self._monte_carlo.simulate(
            counterfactual=counterfactual,
            std_error=std_error,
            iterations=request.monte_carlo_iterations,
        )
        roi = self._roi.calculate(
            counterfactual=counterfactual,
            roi_assumptions=request.roi_assumptions,
        )
        constraint_evals = self._constraints.evaluate(
            constraints=constraints,
            counterfactual=counterfactual,
            roi=roi,
        )
        risk = self._risk.assess(
            counterfactual=counterfactual,
            causal_run=causal_run,
            constraint_evaluations=constraint_evals,
        )

        comparison_entries: list[tuple[str, str, float, float | None, float]] = [
            (str(scenario.id), scenario.name, counterfactual.expected_outcome, roi.expected_roi, risk.overall_score)
        ]
        comparison = self._comparator.compare(comparison_entries)

        interpretation = self._interpreter.interpret(
            objective=request.objective or scenario.objective or request.name,
            scenario_name=scenario.name,
            counterfactual=counterfactual,
            risk=risk,
            roi=roi,
            comparison=comparison,
            extrapolation_warnings=validation.warnings,
        )

        assumptions = (
            "Counterfactual derived from Phase 6 causal treatment effect estimate.",
            "Monte Carlo uses parametric sampling around the point estimate.",
            *causal_assumptions,
            *roi.assumptions,
        )

        return SimulationResultDTO(
            counterfactual=counterfactual,
            monte_carlo=monte_carlo,
            constraint_evaluations=constraint_evals,
            risk=risk,
            roi=roi,
            comparison=comparison,
            interpretation=interpretation,
            assumptions=assumptions,
        )

    @staticmethod
    def _interventions_from_scenario(scenario: SimulationScenario) -> tuple[InterventionDTO, ...]:
        return tuple(
            InterventionDTO(
                variable=i["variable"],
                mode=i.get("mode", "relative"),
                value=i["value"],
                reason=i.get("reason"),
            )
            for i in scenario.interventions
        )

    @staticmethod
    def _constraints_from_scenario(scenario: SimulationScenario) -> tuple[ConstraintDTO, ...]:
        return tuple(
            ConstraintDTO(
                type=c.get("type", "custom"),
                severity=c.get("severity", "soft"),
                threshold=c.get("threshold"),
                description=c.get("description", ""),
                value=c.get("value"),
            )
            for c in scenario.constraints
        )
