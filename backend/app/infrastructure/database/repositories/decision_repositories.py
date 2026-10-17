"""SQLAlchemy decision run repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.decision_run import DecisionRun
from app.domain.repositories.decision_run_repository import DecisionRunRepository
from app.infrastructure.database.mappers.decision import to_decision_run
from app.infrastructure.database.models.decision_run import DecisionRunModel


class SqlAlchemyDecisionRunRepository(DecisionRunRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: DecisionRun) -> DecisionRun:
        model = DecisionRunModel(
            id=run.id,
            dataset_id=run.dataset_id,
            version_id=run.version_id,
            organization_id=run.organization_id,
            project_id=run.project_id,
            created_by=run.created_by,
            status=run.status.value,
            name=run.name,
            primary_objective=run.primary_objective,
            configuration_json=run.configuration,
            result_json=run.result,
            error_message=run.error_message,
            executed_at=run.executed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_decision_run(model)

    async def update(self, run: DecisionRun) -> DecisionRun:
        result = await self._session.execute(
            select(DecisionRunModel).where(DecisionRunModel.id == run.id)
        )
        model = result.scalar_one()
        model.status = run.status.value
        model.configuration_json = run.configuration
        model.result_json = run.result
        model.error_message = run.error_message
        model.executed_at = run.executed_at
        await self._session.flush()
        return to_decision_run(model)

    async def get_by_id(
        self, *, decision_id: UUID, organization_id: UUID
    ) -> DecisionRun | None:
        result = await self._session.execute(
            select(DecisionRunModel).where(
                DecisionRunModel.id == decision_id,
                DecisionRunModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_decision_run(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionRun]:
        result = await self._session.execute(
            select(DecisionRunModel)
            .where(
                DecisionRunModel.dataset_id == dataset_id,
                DecisionRunModel.organization_id == organization_id,
            )
            .order_by(DecisionRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_decision_run(m) for m in result.scalars()]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[DecisionRun]:
        result = await self._session.execute(
            select(DecisionRunModel)
            .where(
                DecisionRunModel.version_id == version_id,
                DecisionRunModel.organization_id == organization_id,
            )
            .order_by(DecisionRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_decision_run(m) for m in result.scalars()]
