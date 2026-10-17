"""Decision session and artifact comparison."""

from __future__ import annotations

from uuid import UUID

from app.application.dto.workspace import ComparisonItemDTO, SessionComparisonDTO
from app.domain.entities.decision_session import DecisionSession
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.domain.repositories.simulation_run_repository import SimulationRunRepository


class ComparisonEngine:
    """Compare sessions, simulations, recommendations, and reports."""

    async def compare_sessions(
        self,
        *,
        session_a: DecisionSession,
        session_b: DecisionSession,
        simulations: SimulationRunRepository,
        decisions: DecisionRunRepository,
        reports: ExecutiveReportRepository,
        organization_id: UUID,
    ) -> SessionComparisonDTO:
        items: list[ComparisonItemDTO] = []

        items.append(
            ComparisonItemDTO(
                label="Session name",
                value_a=session_a.name,
                value_b=session_b.name,
                delta=None,
                highlight=False,
            )
        )
        items.append(
            ComparisonItemDTO(
                label="Status",
                value_a=session_a.status.value,
                value_b=session_b.status.value,
                delta=None,
                highlight=session_a.status != session_b.status,
            )
        )
        items.append(
            ComparisonItemDTO(
                label="Workflow step",
                value_a=session_a.current_step.value,
                value_b=session_b.current_step.value,
                delta=None,
                highlight=session_a.current_step != session_b.current_step,
            )
        )

        roi_a, _ = await self._session_roi(
            session_a, simulations, decisions, organization_id
        )
        roi_b_val, _ = await self._session_roi(
            session_b, simulations, decisions, organization_id
        )
        delta_roi = None
        if roi_a is not None and roi_b_val is not None:
            delta_roi = round(roi_b_val - roi_a, 4)
        items.append(
            ComparisonItemDTO(
                label="Top ROI",
                value_a=roi_a,
                value_b=roi_b_val,
                delta=delta_roi,
                highlight=bool(delta_roi and abs(delta_roi) > 0.05),
            )
        )

        report_a = (
            await reports.get_by_id(
                report_id=session_a.executive_report_id, organization_id=organization_id
            )
            if session_a.executive_report_id
            else None
        )
        report_b = (
            await reports.get_by_id(
                report_id=session_b.executive_report_id, organization_id=organization_id
            )
            if session_b.executive_report_id
            else None
        )
        conf_a = (report_a.result.get("confidence_assessment", {}) if report_a else {}).get(
            "score"
        )
        conf_b = (report_b.result.get("confidence_assessment", {}) if report_b else {}).get(
            "score"
        )
        items.append(
            ComparisonItemDTO(
                label="Confidence score",
                value_a=conf_a,
                value_b=conf_b,
                delta=round(conf_b - conf_a, 3) if conf_a is not None and conf_b is not None else None,
                highlight=bool(
                    conf_a is not None
                    and conf_b is not None
                    and abs(conf_b - conf_a) > 0.1
                ),
            )
        )

        summary = (
            f"Comparing '{session_a.name}' vs '{session_b.name}'. "
            f"Session B is at step {session_b.current_step.value}; "
            f"Session A is at {session_a.current_step.value}."
        )
        return SessionComparisonDTO(
            session_a_id=str(session_a.id),
            session_b_id=str(session_b.id),
            items=tuple(items),
            summary=summary,
        )

    async def _session_roi(
        self,
        session: DecisionSession,
        simulations: SimulationRunRepository,
        decisions: DecisionRunRepository,
        organization_id: UUID,
    ) -> tuple[float | None, float | None]:
        if session.decision_run_id:
            decision = await decisions.get_by_id(
                decision_id=session.decision_run_id, organization_id=organization_id
            )
            if decision and decision.result.get("recommendations"):
                rec = decision.result["recommendations"][0]
                return float(rec.get("roi", 0)), None
        if session.simulation_run_id:
            sim = await simulations.get_by_id(
                simulation_id=session.simulation_run_id, organization_id=organization_id
            )
            if sim:
                roi = sim.result.get("roi", {}).get("expected_roi")
                return float(roi) if roi is not None else None, None
        return None, None
