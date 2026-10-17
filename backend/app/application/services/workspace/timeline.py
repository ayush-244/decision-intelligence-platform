"""Knowledge timeline aggregation."""

from __future__ import annotations

from uuid import UUID

from app.application.dto.workspace import TimelineEventDTO
from app.domain.entities.audit_log import AuditLog
from app.domain.entities.decision_session import DecisionSession
from app.domain.entities.session_activity import SessionActivity
from app.domain.repositories.audit_log_repository import AuditLogRepository
from app.domain.repositories.causal_analysis_repository import CausalAnalysisRepository
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.dag_version_repository import DAGVersionRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.session_activity_repository import SessionActivityRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository


class TimelineEngine:
    """Build chronological knowledge timeline for a session or dataset."""

    def __init__(
        self,
        activities: SessionActivityRepository,
        statistics: StatisticalAnalysisRepository,
        causal: CausalAnalysisRepository,
        dags: DAGVersionRepository,
        simulations: SimulationRunRepository,
        decisions: DecisionRunRepository,
        reports: ExecutiveReportRepository,
        audit_logs: AuditLogRepository,
    ) -> None:
        self._activities = activities
        self._statistics = statistics
        self._causal = causal
        self._dags = dags
        self._simulations = simulations
        self._decisions = decisions
        self._reports = reports
        self._audit_logs = audit_logs

    async def for_session(
        self, *, session: DecisionSession, organization_id: UUID, limit: int = 100
    ) -> tuple[TimelineEventDTO, ...]:
        events: list[TimelineEventDTO] = []

        session_activities = await self._activities.list_for_session(
            session_id=session.id, organization_id=organization_id, limit=limit
        )
        for act in session_activities:
            events.append(self._from_activity(act))

        if session.statistical_analysis_id:
            stat = await self._statistics.get_by_id(
                analysis_id=session.statistical_analysis_id, organization_id=organization_id
            )
            if stat:
                events.append(
                    TimelineEventDTO(
                        id=str(stat.id),
                        event_type="analysis_executed",
                        title=f"Statistical analysis: {stat.goal}",
                        description=stat.result.get("summary") if stat.result else None,
                        resource_type="statistical_analysis",
                        resource_id=str(stat.id),
                        occurred_at=stat.created_at.isoformat(),
                        metadata={},
                    )
                )

        if session.dag_version_id:
            dag = await self._dags.get_by_id(
                dag_id=session.dag_version_id, organization_id=organization_id
            )
            if dag:
                events.append(
                    TimelineEventDTO(
                        id=str(dag.id),
                        event_type="dag_created",
                        title=f"DAG: {dag.name}",
                        description=None,
                        resource_type="dag_version",
                        resource_id=str(dag.id),
                        occurred_at=dag.created_at.isoformat(),
                        metadata={},
                    )
                )

        if session.causal_analysis_id:
            causal = await self._causal.get_by_id(
                analysis_id=session.causal_analysis_id, organization_id=organization_id
            )
            if causal:
                events.append(
                    TimelineEventDTO(
                        id=str(causal.id),
                        event_type="causal_completed",
                        title=f"Causal analysis: {causal.treatment} → {causal.outcome}",
                        description=causal.configuration.get("business_question"),
                        resource_type="causal_analysis",
                        resource_id=str(causal.id),
                        occurred_at=causal.created_at.isoformat(),
                        metadata={},
                    )
                )

        if session.simulation_run_id:
            sim = await self._simulations.get_by_id(
                simulation_id=session.simulation_run_id, organization_id=organization_id
            )
            if sim:
                events.append(
                    TimelineEventDTO(
                        id=str(sim.id),
                        event_type="simulation_completed",
                        title=f"Simulation: {sim.name}",
                        description=None,
                        resource_type="simulation",
                        resource_id=str(sim.id),
                        occurred_at=sim.created_at.isoformat(),
                        metadata={},
                    )
                )

        if session.decision_run_id:
            decision = await self._decisions.get_by_id(
                decision_id=session.decision_run_id, organization_id=organization_id
            )
            if decision:
                events.append(
                    TimelineEventDTO(
                        id=str(decision.id),
                        event_type="recommendation_generated",
                        title=f"Decision: {decision.name}",
                        description=decision.result.get("overall_summary"),
                        resource_type="decision",
                        resource_id=str(decision.id),
                        occurred_at=decision.created_at.isoformat(),
                        metadata={},
                    )
                )

        if session.executive_report_id:
            report = await self._reports.get_by_id(
                report_id=session.executive_report_id, organization_id=organization_id
            )
            if report:
                events.append(
                    TimelineEventDTO(
                        id=str(report.id),
                        event_type="report_generated",
                        title=f"Report: {report.name}",
                        description=report.result.get("executive_summary"),
                        resource_type="executive_report",
                        resource_id=str(report.id),
                        occurred_at=report.created_at.isoformat(),
                        metadata={},
                    )
                )

        events.sort(key=lambda e: e.occurred_at, reverse=True)
        return tuple(events[:limit])

    async def audit_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 30
    ) -> tuple[TimelineEventDTO, ...]:
        logs = await self._audit_logs.list_for_organization(
            organization_id=organization_id, limit=limit * 2
        )
        events = [
            self._from_audit(log)
            for log in logs
            if log.resource_id == dataset_id or log.metadata.get("dataset_id") == str(dataset_id)
        ]
        events.sort(key=lambda e: e.occurred_at, reverse=True)
        return tuple(events[:limit])

    @staticmethod
    def _from_activity(act: SessionActivity) -> TimelineEventDTO:
        return TimelineEventDTO(
            id=str(act.id),
            event_type=act.activity_type.value,
            title=act.title,
            description=act.description,
            resource_type=act.resource_type,
            resource_id=str(act.resource_id) if act.resource_id else None,
            occurred_at=act.created_at.isoformat(),
            metadata=act.metadata,
        )

    @staticmethod
    def _from_audit(log: AuditLog) -> TimelineEventDTO:
        return TimelineEventDTO(
            id=str(log.id),
            event_type=f"audit:{log.action}",
            title=log.action.replace(".", " ").replace("_", " ").title(),
            description=log.resource_type,
            resource_type=log.resource_type,
            resource_id=str(log.resource_id) if log.resource_id else None,
            occurred_at=log.created_at.isoformat(),
            metadata=log.metadata,
        )
