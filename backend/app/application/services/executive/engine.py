"""Executive Report Engine — orchestrates report generation."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.application.dto.executive import ExecutiveReportDTO, GenerateReportRequestDTO
from app.application.services.executive.business_language import BusinessLanguageEngine
from app.application.services.executive.explainability import ExplainabilityEngine
from app.application.services.executive.serialization import to_jsonable
from app.application.services.executive.timeline import TimelineEngine
from app.core.config import Settings
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.decision_run import DecisionRun
from app.domain.entities.executive_report import ExecutiveReport
from app.domain.entities.simulation_run import SimulationRun
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.value_objects.decision import DecisionRunStatus
from app.domain.value_objects.executive import ExecutiveReportStatus
from app.shared.exceptions import BusinessValidationError
from app.shared.utils.datetime import utc_now


class ExecutiveReportEngine:
    """Transform decision intelligence into executive-ready reports."""

    def __init__(
        self,
        settings: Settings,
        reports: ExecutiveReportRepository,
        decisions: DecisionRunRepository,
        simulations: SimulationRunRepository,
        causal_analyses: CausalAnalysisRepository,
    ) -> None:
        self._settings = settings
        self._reports = reports
        self._decisions = decisions
        self._simulations = simulations
        self._causal = causal_analyses
        self._language = BusinessLanguageEngine()
        self._explainability = ExplainabilityEngine()
        self._timeline = TimelineEngine()

    async def generate(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
        decision: DecisionRun,
        request: GenerateReportRequestDTO,
        created_by: UUID,
    ) -> ExecutiveReport:
        now = utc_now()
        version_number = await self._reports.next_version_number(
            dataset_id=dataset.id, name=request.name
        )
        config = to_jsonable(request)
        pending = ExecutiveReport(
            id=uuid4(),
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            decision_run_id=decision.id,
            created_by=created_by,
            status=ExecutiveReportStatus.RUNNING,
            name=request.name,
            business_objective=request.business_objective,
            version_number=version_number,
            configuration=config,
            result={},
            error_message=None,
            executed_at=None,
            created_at=now,
            updated_at=now,
        )
        await self._reports.create(pending)

        try:
            result_dto = await self._build_report(decision=decision, request=request)
            result_dict = to_jsonable(result_dto)
            result_dict["name"] = request.name
            result_dict["include_technical_appendix"] = request.include_technical_appendix
            completed = ExecutiveReport(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                decision_run_id=decision.id,
                created_by=created_by,
                status=ExecutiveReportStatus.COMPLETED,
                name=request.name,
                business_objective=request.business_objective,
                version_number=version_number,
                configuration=config,
                result=result_dict,
                error_message=None,
                executed_at=utc_now(),
                created_at=now,
                updated_at=now,
            )
            return await self._reports.update(completed)
        except Exception as exc:  # noqa: BLE001
            failed = ExecutiveReport(
                id=pending.id,
                dataset_id=dataset.id,
                version_id=version.id,
                organization_id=dataset.organization_id,
                project_id=dataset.project_id,
                decision_run_id=decision.id,
                created_by=created_by,
                status=ExecutiveReportStatus.FAILED,
                name=request.name,
                business_objective=request.business_objective,
                version_number=version_number,
                configuration=config,
                result={},
                error_message=str(exc),
                executed_at=None,
                created_at=now,
                updated_at=now,
            )
            await self._reports.update(failed)
            raise

    async def _build_report(
        self,
        *,
        decision: DecisionRun,
        request: GenerateReportRequestDTO,
    ) -> ExecutiveReportDTO:
        if decision.status is not DecisionRunStatus.COMPLETED:
            raise BusinessValidationError("Decision analysis must be completed.", code="decision_incomplete")

        recs = list(decision.result.get("recommendations", []))
        tradeoffs = tuple(decision.result.get("tradeoffs", []))
        priorities = list(decision.result.get("priorities", []))

        explain_blocks = []
        sim_cache: dict[str, SimulationRun | None] = {}
        causal_cache: dict[str, CausalAnalysisRun | None] = {}

        for rec in recs:
            sim_id = rec.get("evidence", {}).get("simulation_run_id")
            causal_id = rec.get("evidence", {}).get("causal_analysis_id")
            simulation = None
            causal = None
            if sim_id:
                if sim_id not in sim_cache:
                    sim_cache[sim_id] = await self._simulations.get_by_id(
                        simulation_id=UUID(sim_id), organization_id=decision.organization_id
                    )
                simulation = sim_cache[sim_id]
            if causal_id:
                if causal_id not in causal_cache:
                    causal_cache[causal_id] = await self._causal.get_by_id(
                        analysis_id=UUID(causal_id), organization_id=decision.organization_id
                    )
                causal = causal_cache[causal_id]
            explain_blocks.append(
                self._explainability.explain_recommendation(
                    rec=rec, causal=causal, simulation=simulation, decision=decision
                )
            )

        confidence = self._explainability.aggregate_confidence(tuple(explain_blocks))

        top = recs[0] if recs else None
        top_roi = float(top.get("roi", 0)) if top else None
        exec_summary = self._language.executive_summary(
            objective=request.business_objective,
            top_recommendation=top.get("title") if top else None,
            confidence=confidence["level"],
            roi=top_roi,
        )

        key_findings = [
            decision.result.get("overall_summary", ""),
            f"Analyzed {len(recs)} actionable recommendation(s) with {len(decision.result.get('rejected', []))} rejected.",
        ]
        if top:
            key_findings.append(top.get("summary", ""))

        roi_overview = {
            "top_roi": top_roi,
            "narrative": self._language.roi_narrative(
                top_roi or 0,
                float(top.get("decision_score", {}).get("roi", 0)) if top else 0,
                float(top.get("expected_outcome", 0)) if top else 0,
            )
            if top
            else "No ROI projection available.",
        }

        risk_overview = {
            "top_risk": float(top.get("risk", 0)) if top else None,
            "summary": decision.result.get("limitations", ["Review risk tolerance before implementation."])[0]
            if decision.result.get("limitations")
            else "Moderate risk — validate with pilot.",
        }

        scenario_comparison = tuple(
            {
                "title": p.get("title"),
                "priority_score": p.get("priority_score"),
                "rank": p.get("rank"),
            }
            for p in priorities
        )

        roadmap = self._timeline.build_roadmap(recs)
        kpis = (
            {
                "name": "Projected ROI",
                "value": top_roi,
                "unit": "ratio",
            },
            {
                "name": "Confidence",
                "value": confidence["score"],
                "unit": "score",
            },
            {
                "name": "Risk (top recommendation)",
                "value": float(top.get("risk", 0)) if top else None,
                "unit": "score",
            },
        )

        appendix: dict = {}
        if request.include_technical_appendix:
            appendix = {
                "decision_run_id": str(decision.id),
                "decision_result": decision.result,
            }

        narrative = (
            f"What happened? {exec_summary}\n\n"
            f"Why? Evidence flows from statistical analysis through causal identification, "
            f"counterfactual simulation, and decision scoring.\n\n"
            f"How certain? {confidence['summary']}\n\n"
            f"What should we do? Implement recommendations in priority order per the roadmap.\n\n"
            f"What if we do nothing? Status quo outcomes persist; opportunity cost equals projected gains in top scenario."
        )

        return ExecutiveReportDTO(
            executive_summary=exec_summary,
            business_objective=request.business_objective,
            key_findings=tuple(key_findings),
            decision_summary=decision.result.get("overall_summary", ""),
            top_recommendations=tuple(recs[:5]),
            expected_roi=roi_overview,
            expected_risks=risk_overview,
            confidence_assessment=confidence,
            key_assumptions=tuple(decision.result.get("assumptions", [])),
            tradeoffs=tradeoffs,
            scenario_comparison=scenario_comparison,
            implementation_roadmap=roadmap,
            business_kpis=kpis,
            explainability=tuple(explain_blocks),
            appendix=appendix,
            narrative=narrative,
        )
