"""SQLAlchemy executive report repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.executive_report import ExecutiveReport
from app.domain.repositories.executive_report_repository import ExecutiveReportRepository
from app.infrastructure.database.mappers.executive import to_executive_report
from app.infrastructure.database.models.executive_report import ExecutiveReportModel


class SqlAlchemyExecutiveReportRepository(ExecutiveReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, report: ExecutiveReport) -> ExecutiveReport:
        model = ExecutiveReportModel(
            id=report.id,
            dataset_id=report.dataset_id,
            version_id=report.version_id,
            organization_id=report.organization_id,
            project_id=report.project_id,
            decision_run_id=report.decision_run_id,
            created_by=report.created_by,
            status=report.status.value,
            name=report.name,
            business_objective=report.business_objective,
            version_number=report.version_number,
            configuration_json=report.configuration,
            result_json=report.result,
            error_message=report.error_message,
            executed_at=report.executed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_executive_report(model)

    async def update(self, report: ExecutiveReport) -> ExecutiveReport:
        result = await self._session.execute(
            select(ExecutiveReportModel).where(ExecutiveReportModel.id == report.id)
        )
        model = result.scalar_one()
        model.status = report.status.value
        model.configuration_json = report.configuration
        model.result_json = report.result
        model.error_message = report.error_message
        model.executed_at = report.executed_at
        await self._session.flush()
        return to_executive_report(model)

    async def get_by_id(
        self, *, report_id: UUID, organization_id: UUID
    ) -> ExecutiveReport | None:
        result = await self._session.execute(
            select(ExecutiveReportModel).where(
                ExecutiveReportModel.id == report_id,
                ExecutiveReportModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_executive_report(model) if model else None

    async def list_for_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, limit: int = 50
    ) -> list[ExecutiveReport]:
        result = await self._session.execute(
            select(ExecutiveReportModel)
            .where(
                ExecutiveReportModel.dataset_id == dataset_id,
                ExecutiveReportModel.organization_id == organization_id,
            )
            .order_by(ExecutiveReportModel.created_at.desc())
            .limit(limit)
        )
        return [to_executive_report(m) for m in result.scalars()]

    async def next_version_number(self, *, dataset_id: UUID, name: str) -> int:
        result = await self._session.execute(
            select(func.max(ExecutiveReportModel.version_number)).where(
                ExecutiveReportModel.dataset_id == dataset_id,
                ExecutiveReportModel.name == name,
            )
        )
        current = result.scalar()
        return (current or 0) + 1
