"""SQLAlchemy workspace repositories."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.decision_session import DecisionSession
from app.domain.entities.session_activity import SessionActivity
from app.domain.repositories.decision_session_repository import DecisionSessionRepository
from app.domain.repositories.session_activity_repository import SessionActivityRepository
from app.infrastructure.database.mappers.workspace import to_decision_session, to_session_activity
from app.infrastructure.database.models.decision_session import DecisionSessionModel, SessionActivityModel


class SqlAlchemyDecisionSessionRepository(DecisionSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, session: DecisionSession) -> DecisionSession:
        model = DecisionSessionModel(
            id=session.id,
            dataset_id=session.dataset_id,
            version_id=session.version_id,
            organization_id=session.organization_id,
            project_id=session.project_id,
            created_by=session.created_by,
            name=session.name,
            description=session.description,
            status=session.status.value,
            version_number=session.version_number,
            current_step=session.current_step.value,
            statistical_analysis_id=session.statistical_analysis_id,
            dag_version_id=session.dag_version_id,
            causal_analysis_id=session.causal_analysis_id,
            simulation_run_id=session.simulation_run_id,
            decision_run_id=session.decision_run_id,
            executive_report_id=session.executive_report_id,
            workspace_state_json=session.workspace_state,
            configuration_json=session.configuration,
            paused_at=session.paused_at,
            completed_at=session.completed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_decision_session(model)

    async def update(self, session: DecisionSession) -> DecisionSession:
        result = await self._session.execute(
            select(DecisionSessionModel).where(DecisionSessionModel.id == session.id)
        )
        model = result.scalar_one()
        model.name = session.name
        model.description = session.description
        model.status = session.status.value
        model.current_step = session.current_step.value
        model.statistical_analysis_id = session.statistical_analysis_id
        model.dag_version_id = session.dag_version_id
        model.causal_analysis_id = session.causal_analysis_id
        model.simulation_run_id = session.simulation_run_id
        model.decision_run_id = session.decision_run_id
        model.executive_report_id = session.executive_report_id
        model.workspace_state_json = session.workspace_state
        model.configuration_json = session.configuration
        model.paused_at = session.paused_at
        model.completed_at = session.completed_at
        await self._session.flush()
        return to_decision_session(model)

    async def get_by_id(
        self, *, session_id: UUID, organization_id: UUID
    ) -> DecisionSession | None:
        result = await self._session.execute(
            select(DecisionSessionModel).where(
                DecisionSessionModel.id == session_id,
                DecisionSessionModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_decision_session(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionSession]:
        result = await self._session.execute(
            select(DecisionSessionModel)
            .where(
                DecisionSessionModel.dataset_id == dataset_id,
                DecisionSessionModel.organization_id == organization_id,
            )
            .order_by(DecisionSessionModel.created_at.desc())
            .limit(limit)
        )
        return [to_decision_session(m) for m in result.scalars()]

    async def search_by_name(
        self, *, organization_id: UUID, query: str, limit: int = 20
    ) -> list[DecisionSession]:
        pattern = f"%{query}%"
        result = await self._session.execute(
            select(DecisionSessionModel)
            .where(
                DecisionSessionModel.organization_id == organization_id,
                or_(
                    DecisionSessionModel.name.ilike(pattern),
                    DecisionSessionModel.description.ilike(pattern),
                ),
            )
            .order_by(DecisionSessionModel.created_at.desc())
            .limit(limit)
        )
        return [to_decision_session(m) for m in result.scalars()]

    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int:
        result = await self._session.execute(
            select(func.max(DecisionSessionModel.version_number)).where(
                DecisionSessionModel.dataset_id == dataset_id,
                DecisionSessionModel.name == name,
            )
        )
        current = result.scalar()
        return (current or 0) + 1


class SqlAlchemySessionActivityRepository(SessionActivityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, activity: SessionActivity) -> SessionActivity:
        model = SessionActivityModel(
            id=activity.id,
            session_id=activity.session_id,
            organization_id=activity.organization_id,
            user_id=activity.user_id,
            activity_type=activity.activity_type.value,
            title=activity.title,
            description=activity.description,
            resource_type=activity.resource_type,
            resource_id=activity.resource_id,
            metadata_json=activity.metadata,
        )
        self._session.add(model)
        await self._session.flush()
        return to_session_activity(model)

    async def list_for_session(
        self, *, session_id: UUID, organization_id: UUID, limit: int = 100
    ) -> list[SessionActivity]:
        result = await self._session.execute(
            select(SessionActivityModel)
            .where(
                SessionActivityModel.session_id == session_id,
                SessionActivityModel.organization_id == organization_id,
            )
            .order_by(SessionActivityModel.created_at.desc())
            .limit(limit)
        )
        return [to_session_activity(m) for m in result.scalars()]
