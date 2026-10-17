"""Build structured, verified context from Delphi analytical outputs."""

from __future__ import annotations

from uuid import UUID

from app.application.dto.copilot import StructuredContext
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.dataset_repository import DatasetRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.decision_session_repository import DecisionSessionRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository
from app.shared.exceptions import NotFoundError


class CopilotContextBuilder:
    """Assemble tenant-scoped analytical context — never accesses DB directly from LLM."""

    def __init__(
        self,
        datasets: DatasetRepository,
        intelligence: IntelligenceReportRepository,
        statistics: StatisticalAnalysisRepository,
        causal: CausalAnalysisRepository,
        simulations: SimulationRunRepository,
        decisions: DecisionRunRepository,
        reports: ExecutiveReportRepository,
        sessions: DecisionSessionRepository,
    ) -> None:
        self._datasets = datasets
        self._intelligence = intelligence
        self._statistics = statistics
        self._causal = causal
        self._simulations = simulations
        self._decisions = decisions
        self._reports = reports
        self._sessions = sessions

    async def build(
        self,
        *,
        organization_id: UUID,
        dataset_id: UUID | None = None,
        session_id: UUID | None = None,
    ) -> StructuredContext:
        ctx = StructuredContext()
        if dataset_id is None:
            return ctx

        dataset = await self._datasets.get_by_id(
            dataset_id=dataset_id, organization_id=organization_id
        )
        if dataset is None:
            raise NotFoundError("Dataset not found.")

        ctx = StructuredContext(
            dataset={
                "id": str(dataset.id),
                "name": dataset.name,
            }
        )

        intel = await self._intelligence.get_by_dataset(
            dataset_id=dataset_id, organization_id=organization_id
        )
        if intel:
            ctx = _replace(ctx, data_quality={
                "health_score": intel.health_score,
                "quality_score": intel.quality_score,
                "report_id": str(intel.id),
            })
            ctx.evidence_index[f"intelligence:{intel.id}"] = {
                "type": "intelligence_report",
                "id": str(intel.id),
                "health_score": intel.health_score,
                "quality_score": intel.quality_score,
            }

        stats = await self._statistics.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=5
        )
        stat_entries = []
        for i, run in enumerate(stats, start=1):
            summary = _stat_summary(run.result)
            entry = {
                "id": str(run.id),
                "short_id": i,
                "goal": run.goal,
                "test_type": run.test_type.value if run.test_type else None,
                "summary": summary,
                "result": _safe_result_slice(run.result),
            }
            stat_entries.append(entry)
            ctx.evidence_index[f"statistical:{run.id}"] = entry
        ctx = _replace(ctx, statistics=stat_entries)

        causal_runs = await self._causal.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=3
        )
        causal_entries = []
        for i, run in enumerate(causal_runs, start=1):
            cfg = run.configuration
            entry = {
                "id": str(run.id),
                "short_id": i,
                "treatment": cfg.get("treatment_variable"),
                "outcome": cfg.get("outcome_variable"),
                "summary": _causal_summary(run.result),
                "result": _safe_result_slice(run.result),
            }
            causal_entries.append(entry)
            ctx.evidence_index[f"causal:{run.id}"] = entry
        ctx = _replace(ctx, causal=causal_entries)

        sims = await self._simulations.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=3
        )
        sim_entries = []
        for i, run in enumerate(sims, start=1):
            entry = {
                "id": str(run.id),
                "short_id": i,
                "name": run.name,
                "summary": _simulation_summary(run.result),
                "result": _safe_result_slice(run.result),
            }
            sim_entries.append(entry)
            ctx.evidence_index[f"simulation:{run.id}"] = entry
        ctx = _replace(ctx, simulations=sim_entries)

        decision_runs = await self._decisions.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=3
        )
        decision_entries = []
        for i, run in enumerate(decision_runs, start=1):
            recs = run.result.get("recommendations", [])
            top = recs[0] if recs else {}
            entry = {
                "id": str(run.id),
                "short_id": i,
                "objective": run.primary_objective,
                "top_recommendation": top.get("title") or top.get("name"),
                "recommendations": recs[:5],
                "result": _safe_result_slice(run.result),
            }
            decision_entries.append(entry)
            ctx.evidence_index[f"decision:{run.id}"] = entry
        ctx = _replace(ctx, decisions=decision_entries)

        exec_reports = await self._reports.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=2
        )
        report_entries = []
        for i, report in enumerate(exec_reports, start=1):
            entry = {
                "id": str(report.id),
                "short_id": i,
                "name": report.name,
                "summary": report.result.get("executive_summary", "")[:500],
                "result": _safe_result_slice(report.result),
            }
            report_entries.append(entry)
            ctx.evidence_index[f"report:{report.id}"] = entry
        ctx = _replace(ctx, reports=report_entries)

        if session_id:
            session = await self._sessions.get_by_id(
                session_id=session_id, organization_id=organization_id
            )
            if session:
                session_entry = {
                    "id": str(session.id),
                    "name": session.name,
                    "current_step": session.current_step,
                    "status": session.status.value,
                }
                ctx = _replace(ctx, session=session_entry)
                ctx.evidence_index[f"session:{session.id}"] = session_entry

        return ctx


def _replace(ctx: StructuredContext, **kwargs) -> StructuredContext:
    from dataclasses import replace

    return replace(ctx, **kwargs)


def _safe_result_slice(result: dict, max_keys: int = 12) -> dict:
    if not result:
        return {}
    keys = list(result.keys())[:max_keys]
    return {k: result[k] for k in keys if not str(k).startswith("_")}


def _stat_summary(result: dict) -> str:
    interp = result.get("interpretation") or result.get("business_interpretation")
    if isinstance(interp, str):
        return interp[:300]
    p_value = result.get("p_value")
    if p_value is not None:
        return f"p-value={p_value}"
    return "Analysis completed."


def _causal_summary(result: dict) -> str:
    ate = result.get("ate") or result.get("average_treatment_effect")
    if ate is not None:
        return f"Estimated ATE: {ate}"
    return result.get("summary", "Causal analysis completed.")[:300]


def _simulation_summary(result: dict) -> str:
    expected = result.get("expected_outcome") or result.get("expected_value")
    if expected is not None:
        return f"Expected outcome: {expected}"
    return result.get("summary", "Simulation completed.")[:300]
