"""SQLAlchemy statistical analysis repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.statistical_analysis import StatisticalAnalysisRun
from app.domain.repositories.statistical_analysis_repository import StatisticalAnalysisRepository
from app.infrastructure.database.mappers.statistics import to_statistical_analysis_run
from app.infrastructure.database.models.statistical_analysis import StatisticalAnalysisRunModel


class SqlAlchemyStatisticalAnalysisRepository(StatisticalAnalysisRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, run: StatisticalAnalysisRun) -> StatisticalAnalysisRun:
        model = StatisticalAnalysisRunModel(
            id=run.id,
            dataset_id=run.dataset_id,
            version_id=run.version_id,
            organization_id=run.organization_id,
            project_id=run.project_id,
            created_by=run.created_by,
            status=run.status.value,
            goal=run.goal,
            test_type=run.test_type.value if run.test_type else None,
            configuration_json=run.configuration,
            result_json=run.result,
            error_message=run.error_message,
            executed_at=run.executed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_statistical_analysis_run(model)

    async def update(self, run: StatisticalAnalysisRun) -> StatisticalAnalysisRun:
        result = await self._session.execute(
            select(StatisticalAnalysisRunModel).where(StatisticalAnalysisRunModel.id == run.id)
        )
        model = result.scalar_one()
        model.status = run.status.value
        model.goal = run.goal
        model.test_type = run.test_type.value if run.test_type else None
        model.configuration_json = run.configuration
        model.result_json = run.result
        model.error_message = run.error_message
        model.executed_at = run.executed_at
        await self._session.flush()
        return to_statistical_analysis_run(model)

    async def get_by_id(
        self, *, analysis_id: UUID, organization_id: UUID
    ) -> StatisticalAnalysisRun | None:
        result = await self._session.execute(
            select(StatisticalAnalysisRunModel).where(
                StatisticalAnalysisRunModel.id == analysis_id,
                StatisticalAnalysisRunModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_statistical_analysis_run(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[StatisticalAnalysisRun]:
        result = await self._session.execute(
            select(StatisticalAnalysisRunModel)
            .where(
                StatisticalAnalysisRunModel.dataset_id == dataset_id,
                StatisticalAnalysisRunModel.organization_id == organization_id,
            )
            .order_by(StatisticalAnalysisRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_statistical_analysis_run(m) for m in result.scalars().all()]

    async def list_for_version(
        self, *, version_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[StatisticalAnalysisRun]:
        result = await self._session.execute(
            select(StatisticalAnalysisRunModel)
            .where(
                StatisticalAnalysisRunModel.version_id == version_id,
                StatisticalAnalysisRunModel.organization_id == organization_id,
            )
            .order_by(StatisticalAnalysisRunModel.created_at.desc())
            .limit(limit)
        )
        return [to_statistical_analysis_run(m) for m in result.scalars().all()]
