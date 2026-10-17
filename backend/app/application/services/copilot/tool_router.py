"""Route tool invocations to application services — never direct DB access."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.domain.value_objects.copilot import CopilotToolName
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.decision_session_repository import DecisionSessionRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository
from app.shared.exceptions import NotFoundError


class CopilotToolRouter:
    """Execute named tools against authorized repositories."""

    def __init__(
        self,
        statistics: StatisticalAnalysisRepository,
        causal: CausalAnalysisRepository,
        simulations: SimulationRunRepository,
        decisions: DecisionRunRepository,
        reports: ExecutiveReportRepository,
        intelligence: IntelligenceReportRepository,
        sessions: DecisionSessionRepository,
    ) -> None:
        self._statistics = statistics
        self._causal = causal
        self._simulations = simulations
        self._decisions = decisions
        self._reports = reports
        self._intelligence = intelligence
        self._sessions = sessions

    async def invoke(
        self,
        *,
        tool: CopilotToolName,
        organization_id: UUID,
        dataset_id: UUID | None = None,
        resource_id: UUID | None = None,
    ) -> dict[str, Any]:
        handlers = {
            CopilotToolName.GET_STATISTICAL_ANALYSIS: self._get_statistical,
            CopilotToolName.GET_CAUSAL_ANALYSIS: self._get_causal,
            CopilotToolName.GET_SIMULATION: self._get_simulation,
            CopilotToolName.GET_DECISION: self._get_decision,
            CopilotToolName.GET_EXECUTIVE_REPORT: self._get_report,
            CopilotToolName.GET_DATA_QUALITY: self._get_data_quality,
            CopilotToolName.GET_DECISION_SESSION: self._get_session,
            CopilotToolName.LIST_RECOMMENDATIONS: self._list_recommendations,
        }
        handler = handlers.get(tool)
        if handler is None:
            raise NotFoundError(f"Unknown tool: {tool}")
        return await handler(
            organization_id=organization_id,
            dataset_id=dataset_id,
            resource_id=resource_id,
        )

    async def _get_statistical(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if resource_id is None:
            raise NotFoundError("resource_id required")
        run = await self._statistics.get_by_id(
            analysis_id=resource_id, organization_id=organization_id
        )
        if run is None:
            raise NotFoundError("Statistical analysis not found.")
        return {"id": str(run.id), "goal": run.goal, "result": run.result}

    async def _get_causal(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if resource_id is None:
            raise NotFoundError("resource_id required")
        run = await self._causal.get_by_id(
            analysis_id=resource_id, organization_id=organization_id
        )
        if run is None:
            raise NotFoundError("Causal analysis not found.")
        return {"id": str(run.id), "configuration": run.configuration, "result": run.result}

    async def _get_simulation(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if resource_id is None:
            raise NotFoundError("resource_id required")
        run = await self._simulations.get_by_id(
            simulation_id=resource_id, organization_id=organization_id
        )
        if run is None:
            raise NotFoundError("Simulation not found.")
        return {"id": str(run.id), "name": run.name, "result": run.result}

    async def _get_decision(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if resource_id is None:
            raise NotFoundError("resource_id required")
        run = await self._decisions.get_by_id(
            decision_id=resource_id, organization_id=organization_id
        )
        if run is None:
            raise NotFoundError("Decision run not found.")
        return {
            "id": str(run.id),
            "objective": run.primary_objective,
            "recommendations": run.result.get("recommendations", []),
            "result": run.result,
        }

    async def _get_report(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if resource_id is None:
            raise NotFoundError("resource_id required")
        report = await self._reports.get_by_id(
            report_id=resource_id, organization_id=organization_id
        )
        if report is None:
            raise NotFoundError("Executive report not found.")
        return {"id": str(report.id), "name": report.name, "result": report.result}

    async def _get_data_quality(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if dataset_id is None:
            raise NotFoundError("dataset_id required")
        report = await self._intelligence.get_by_dataset(
            dataset_id=dataset_id, organization_id=organization_id
        )
        if report is None:
            raise NotFoundError("Data quality report not found.")
        return {
            "health_score": report.health_score,
            "quality_score": report.quality_score,
            "report_id": str(report.id),
        }

    async def _get_session(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if resource_id is None:
            raise NotFoundError("resource_id required")
        session = await self._sessions.get_by_id(
            session_id=resource_id, organization_id=organization_id
        )
        if session is None:
            raise NotFoundError("Decision session not found.")
        return {
            "id": str(session.id),
            "name": session.name,
            "current_step": session.current_step,
            "status": session.status.value,
        }

    async def _list_recommendations(
        self, *, organization_id: UUID, dataset_id: UUID | None, resource_id: UUID | None
    ) -> dict[str, Any]:
        if dataset_id is None:
            raise NotFoundError("dataset_id required")
        runs = await self._decisions.list_for_dataset(
            dataset_id=dataset_id, organization_id=organization_id, limit=1
        )
        if not runs:
            return {"recommendations": []}
        return {"recommendations": runs[0].result.get("recommendations", [])}
