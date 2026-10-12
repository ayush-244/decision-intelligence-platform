"""Decision Intelligence Engine — orchestrates evidence-based recommendations."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.application.dto.decision import DecisionRequestDTO, DecisionResultDTO, RecommendationDTO
from app.application.services.decision.constraint_manager import ConstraintManager
from app.application.services.decision.explanation import ExplanationEngine
from app.application.services.decision.objective_analyzer import ObjectiveAnalyzer
from app.application.services.decision.optimization import OptimizationEngine
from app.application.services.decision.priority import PriorityEngine
from app.application.services.decision.recommendation import RecommendationGenerator
from app.application.services.decision.scoring import DecisionScorer
from app.application.services.decision.serialization import to_jsonable
from app.application.services.decision.tradeoff import TradeoffEngine
from app.application.services.decision.validator import DecisionValidator
from app.core.config import Settings
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.decision_run import DecisionRun
from app.domain.entities.simulation_run import SimulationRun
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.value_objects.decision import DecisionRunStatus, RecommendationStatus
from app.domain.value_objects.simulation import SimulationRunStatus
from app.shared.exceptions import BusinessValidationError
from app.shared.utils.datetime import utc_now


class DecisionEngine:
    """Transform evidence into ranked, explainable business recommendations."""

    def __init__(
        self,
        settings: Settings,
        decisions: DecisionRunRepository,
        simulations: SimulationRunRepository,
        causal_analyses: CausalAnalysisRepository,
    ) -> None:
        self._settings = settings
        self._decisions = decisions
        self._simulations = simulations
        self._causal = causal_analyses
        self._objectives = ObjectiveAnalyzer()
        self._constraints = ConstraintManager()
        self._scorer = DecisionScorer()
        self._optimizer = OptimizationEngine()
        self._tradeoffs = TradeoffEngine()
        self._priority = PriorityEngine()
        self._recommendations = RecommendationGenerator()
        self._validator = DecisionValidator()
        self._explainer = ExplanationEngine()

    async def analyze(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
        request: DecisionRequestDTO,
        simulation_runs: list[SimulationRun],
        created_by: UUID,
    ) -> DecisionRun:
        now = utc_now()
        config = to_jsonable(request)
        pending = DecisionRun(
            id=uuid4(),
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            created_by=created_by,
            status=DecisionRunStatus.RUNNING,
            name=request.name,
            primary_objective=request.primary_objective,
            configuration=config,
            result={},
            error_message=None,
            executed_at=None,
            created_at=now,
            updated_at=now,
        )
        await self._decisions.create(pending)

        try:
            result_dto = await self._run_pipeline(request=request, simulation_runs=simulation_runs)
            result_dict = to_jsonable(result_dto)
            completed = DecisionRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                created_by=created_by,
                status=DecisionRunStatus.COMPLETED,
                name=request.name,
                primary_objective=request.primary_objective,
                configuration=config,
                result=result_dict,
                error_message=None,
                executed_at=utc_now(),
                created_at=now,
                updated_at=now,
            )
            return await self._decisions.update(completed)
        except Exception as exc:  # noqa: BLE001
            failed = DecisionRun(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                created_by=created_by,
                status=DecisionRunStatus.FAILED,
                name=request.name,
                primary_objective=request.primary_objective,
                configuration=config,
                result={},
                error_message=str(exc),
                executed_at=None,
                created_at=now,
                updated_at=now,
            )
            await self._decisions.update(failed)
            raise

    async def _run_pipeline(
        self,
        *,
        request: DecisionRequestDTO,
        simulation_runs: list[SimulationRun],
    ) -> DecisionResultDTO:
        if not simulation_runs:
            raise BusinessValidationError(
                "At least one completed simulation is required.", code="no_simulations"
            )

        primary, weights = self._objectives.analyze(request)
        candidates: list[RecommendationDTO] = []
        rejected: list[RecommendationDTO] = []
        all_constraint_evals: list[dict[str, object]] = []

        deltas: list[float] = []
        for sim in simulation_runs:
            cf = (sim.result or {}).get("counterfactual", {})
            baseline = float(cf.get("baseline_outcome", 0))
            expected = float(cf.get("expected_outcome", baseline))
            deltas.append(abs(expected - baseline))
        max_delta = max(deltas) if deltas else 1.0

        for idx, sim in enumerate(simulation_runs, start=1):
            if sim.status is not SimulationRunStatus.COMPLETED:
                continue
            causal = await self._causal.get_by_id(
                analysis_id=sim.causal_analysis_id,
                organization_id=sim.organization_id,
            )
            if causal is None:
                continue

            evals, constraints_ok, constraint_sat = self._constraints.evaluate(
                constraints=request.constraints,
                simulation=sim,
                risk_tolerance=request.risk_tolerance,
                min_confidence=request.min_confidence,
                max_budget=request.max_budget,
            )
            all_constraint_evals.extend(evals)

            cf = sim.result.get("counterfactual", {})
            roi = float(sim.result.get("roi", {}).get("expected_roi", 0))
            risk = float(sim.result.get("risk", {}).get("overall_score", 0.5))
            confidence = 1.0 - float(cf.get("uncertainty_score", 0.5))
            baseline = float(cf.get("baseline_outcome", 0))
            expected = float(cf.get("expected_outcome", baseline))
            outcome_delta = expected - baseline

            alignment = self._objectives.alignment_score(
                primary_objective=primary,
                outcome_delta=outcome_delta,
                roi=roi,
                risk=risk,
                weights=weights,
            )
            feasibility = 0.8 if constraints_ok else 0.4

            score = self._scorer.score(
                outcome_delta=outcome_delta,
                max_delta=max_delta,
                roi=roi,
                confidence=confidence,
                risk=risk,
                feasibility=feasibility,
                strategic_alignment=alignment,
                constraint_satisfaction=constraint_sat,
            )

            identified = bool(causal.result.get("identification", {}).get("identified", False))
            draft = self._recommendations.build(
                simulation=sim,
                causal=causal,
                rank=idx,
                decision_score=score,
                status=RecommendationStatus.APPROVED.value,
                validation_passed=True,
                validation_notes="",
                strategic_alignment=alignment,
            )
            passed, status, notes = self._validator.validate(
                recommendation=draft,
                min_confidence=request.min_confidence,
                risk_tolerance=request.risk_tolerance,
                constraints_satisfied=constraints_ok,
                causal_identified=identified,
            )
            final = RecommendationDTO(
                rank=draft.rank,
                status=status,
                title=draft.title,
                summary=draft.summary,
                reason=draft.reason,
                evidence=draft.evidence,
                expected_outcome=draft.expected_outcome,
                confidence=draft.confidence,
                roi=draft.roi,
                risk=draft.risk,
                required_assumptions=draft.required_assumptions,
                implementation_difficulty=draft.implementation_difficulty,
                expected_timeline=draft.expected_timeline,
                dependencies=draft.dependencies,
                alternative_options=draft.alternative_options,
                business_explanation=draft.business_explanation,
                recommended_order=draft.recommended_order,
                decision_score=draft.decision_score,
                validation_passed=passed,
                validation_notes=(notes,),
            )
            if status == RecommendationStatus.REJECTED.value:
                rejected.append(final)
            else:
                candidates.append(final)

        ranked = self._optimizer.rank(candidates)
        ranked_list: list[RecommendationDTO] = []
        for i, rec in enumerate(ranked, start=1):
            ranked_list.append(
                RecommendationDTO(
                    rank=i,
                    status=rec.status,
                    title=rec.title,
                    summary=rec.summary,
                    reason=rec.reason,
                    evidence=rec.evidence,
                    expected_outcome=rec.expected_outcome,
                    confidence=rec.confidence,
                    roi=rec.roi,
                    risk=rec.risk,
                    required_assumptions=rec.required_assumptions,
                    implementation_difficulty=rec.implementation_difficulty,
                    expected_timeline=rec.expected_timeline,
                    dependencies=rec.dependencies,
                    alternative_options=rec.alternative_options,
                    business_explanation=rec.business_explanation,
                    recommended_order=i,
                    decision_score=rec.decision_score,
                    validation_passed=rec.validation_passed,
                    validation_notes=rec.validation_notes,
                )
            )
        ranked = tuple(ranked_list)

        tradeoffs = self._tradeoffs.analyze(ranked)
        priorities = self._priority.prioritize(ranked)
        summary, first, limitations = self._explainer.summarize(
            primary_objective=primary,
            recommendations=ranked,
            rejected_count=len(rejected),
        )
        deferred = tuple(r.title for r in ranked if r.status == RecommendationStatus.DEFERRED.value)

        return DecisionResultDTO(
            recommendations=ranked,
            rejected=tuple(rejected),
            tradeoffs=tradeoffs,
            priorities=priorities,
            objectives_analyzed=tuple(weights.keys()),
            constraint_evaluations=tuple(all_constraint_evals),
            overall_summary=summary,
            recommended_first=first,
            deferred=deferred,
            assumptions=(
                "Every recommendation requires completed causal identification and simulation.",
                "Scores combine business impact, ROI, confidence, risk, feasibility, alignment.",
            ),
            limitations=limitations,
        )
