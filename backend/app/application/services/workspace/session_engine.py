"""Decision session orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any
from uuid import UUID, uuid4

from app.application.dto.workspace import WorkflowProgressDTO
from app.application.services.workspace.serialization import to_jsonable
from app.domain.entities.dataset import Dataset
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.entities.decision_session import DecisionSession
from app.domain.entities.session_activity import SessionActivity
from app.domain.repositories.decision_session_repository import DecisionSessionRepository
from app.domain.repositories.session_activity_repository import SessionActivityRepository
from app.domain.value_objects.workspace import (
    WORKFLOW_STEP_ORDER,
    DecisionSessionStatus,
    SessionActivityType,
    WorkflowStep,
)
from app.shared.utils.datetime import utc_now


class DecisionSessionEngine:
    """Create and manage decision sessions that preserve the analytical journey."""

    def __init__(
        self,
        sessions: DecisionSessionRepository,
        activities: SessionActivityRepository,
    ) -> None:
        self._sessions = sessions
        self._activities = activities

    async def create(
        self,
        *,
        dataset: Dataset,
        version: DatasetVersion,
        name: str,
        description: str | None,
        created_by: UUID,
        configuration: dict[str, Any] | None = None,
    ) -> DecisionSession:
        now = utc_now()
        version_number = await self._sessions.next_version_number(
            dataset_id=dataset.id, name=name
        )
        session = DecisionSession(
            id=uuid4(),
            dataset_id=dataset.id,
            version_id=version.id,
            organization_id=dataset.organization_id,
            project_id=dataset.project_id,
            created_by=created_by,
            name=name,
            description=description,
            status=DecisionSessionStatus.ACTIVE,
            version_number=version_number,
            current_step=WorkflowStep.SELECT_VERSION,
            statistical_analysis_id=None,
            dag_version_id=None,
            causal_analysis_id=None,
            simulation_run_id=None,
            decision_run_id=None,
            executive_report_id=None,
            workspace_state=self._default_workspace_state(),
            configuration=configuration or {},
            paused_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        created = await self._sessions.create(session)
        await self._record_activity(
            session=created,
            user_id=created_by,
            activity_type=SessionActivityType.SESSION_CREATED,
            title=f"Session '{name}' created",
            description="Decision session started.",
        )
        return created

    async def update(
        self,
        *,
        session: DecisionSession,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
        current_step: WorkflowStep | None = None,
        workspace_state: dict[str, Any] | None = None,
        statistical_analysis_id: UUID | None = None,
        dag_version_id: UUID | None = None,
        causal_analysis_id: UUID | None = None,
        simulation_run_id: UUID | None = None,
        decision_run_id: UUID | None = None,
        executive_report_id: UUID | None = None,
        link_only: bool = False,
    ) -> DecisionSession:
        now = utc_now()
        updated = DecisionSession(
            id=session.id,
            dataset_id=session.dataset_id,
            version_id=session.version_id,
            organization_id=session.organization_id,
            project_id=session.project_id,
            created_by=session.created_by,
            name=name if name is not None else session.name,
            description=description if description is not None else session.description,
            status=session.status,
            version_number=session.version_number,
            current_step=current_step if current_step is not None else session.current_step,
            statistical_analysis_id=(
                statistical_analysis_id
                if statistical_analysis_id is not None
                else session.statistical_analysis_id
            ),
            dag_version_id=(
                dag_version_id if dag_version_id is not None else session.dag_version_id
            ),
            causal_analysis_id=(
                causal_analysis_id
                if causal_analysis_id is not None
                else session.causal_analysis_id
            ),
            simulation_run_id=(
                simulation_run_id
                if simulation_run_id is not None
                else session.simulation_run_id
            ),
            decision_run_id=(
                decision_run_id if decision_run_id is not None else session.decision_run_id
            ),
            executive_report_id=(
                executive_report_id
                if executive_report_id is not None
                else session.executive_report_id
            ),
            workspace_state=(
                workspace_state if workspace_state is not None else session.workspace_state
            ),
            configuration=session.configuration,
            paused_at=session.paused_at,
            completed_at=session.completed_at,
            created_at=session.created_at,
            updated_at=now,
        )
        result = await self._sessions.update(updated)
        if current_step is not None and not link_only:
            await self._record_activity(
                session=result,
                user_id=user_id,
                activity_type=SessionActivityType.STEP_COMPLETED,
                title=f"Advanced to {current_step.value.replace('_', ' ')}",
                description=None,
                metadata={"step": current_step.value},
            )
        return result

    async def pause(self, *, session: DecisionSession, user_id: UUID) -> DecisionSession:
        now = utc_now()
        paused = replace(
            session,
            status=DecisionSessionStatus.PAUSED,
            paused_at=now,
            updated_at=now,
        )
        result = await self._sessions.update(paused)
        await self._record_activity(
            session=result,
            user_id=user_id,
            activity_type=SessionActivityType.SESSION_PAUSED,
            title="Session paused",
            description=None,
        )
        return result

    async def resume(self, *, session: DecisionSession, user_id: UUID) -> DecisionSession:
        now = utc_now()
        resumed = replace(
            session,
            status=DecisionSessionStatus.ACTIVE,
            paused_at=None,
            updated_at=now,
        )
        result = await self._sessions.update(resumed)
        await self._record_activity(
            session=result,
            user_id=user_id,
            activity_type=SessionActivityType.SESSION_RESUMED,
            title="Session resumed",
            description=None,
        )
        return result

    async def complete(self, *, session: DecisionSession, user_id: UUID) -> DecisionSession:
        now = utc_now()
        completed = replace(
            session,
            status=DecisionSessionStatus.COMPLETED,
            current_step=WorkflowStep.SAVE_SESSION,
            completed_at=now,
            updated_at=now,
        )
        result = await self._sessions.update(completed)
        await self._record_activity(
            session=result,
            user_id=user_id,
            activity_type=SessionActivityType.SESSION_COMPLETED,
            title="Session completed",
            description="Analytical journey saved.",
        )
        return result

    def progress(self, session: DecisionSession) -> WorkflowProgressDTO:
        order = WORKFLOW_STEP_ORDER
        try:
            idx = order.index(session.current_step)
        except ValueError:
            idx = 0
        completed = tuple(s.value for s in order[: idx + 1])
        total = len(order)
        percent = round((idx + 1) / total * 100, 1)
        next_step = order[idx + 1].value if idx + 1 < total else None
        return WorkflowProgressDTO(
            current_step=session.current_step.value,
            completed_steps=completed,
            total_steps=total,
            percent_complete=percent,
            next_step=next_step,
        )

    async def add_comment(
        self,
        *,
        session: DecisionSession,
        user_id: UUID,
        body: str,
        mentions: tuple[str, ...] = (),
    ) -> SessionActivity:
        return await self._record_activity(
            session=session,
            user_id=user_id,
            activity_type=SessionActivityType.COMMENT,
            title="Comment added",
            description=body,
            metadata={"mentions": list(mentions), "collaboration": "foundation"},
        )

    @staticmethod
    def _default_workspace_state() -> dict[str, Any]:
        return {
            "panels": {
                "sidebar": True,
                "context": True,
                "timeline": True,
                "evidence": False,
            },
            "canvas": {
                "nodes": [],
                "active_node": None,
            },
            "comparison": None,
        }

    async def _record_activity(
        self,
        *,
        session: DecisionSession,
        user_id: UUID | None,
        activity_type: SessionActivityType,
        title: str,
        description: str | None,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionActivity:
        activity = SessionActivity(
            id=uuid4(),
            session_id=session.id,
            organization_id=session.organization_id,
            user_id=user_id,
            activity_type=activity_type,
            title=title,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=to_jsonable(metadata or {}),
            created_at=utc_now(),
        )
        return await self._activities.append(activity)
