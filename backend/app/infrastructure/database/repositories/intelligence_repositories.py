"""SQLAlchemy intelligence report repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.intelligence_report import IntelligenceReport
from app.domain.repositories.intelligence_report_repository import IntelligenceReportRepository
from app.infrastructure.database.mappers.intelligence import to_intelligence_report
from app.infrastructure.database.models.intelligence_report import IntelligenceReportModel


class SqlAlchemyIntelligenceReportRepository(IntelligenceReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_version(self, *, version_id: UUID) -> IntelligenceReport | None:
        result = await self._session.execute(
            select(IntelligenceReportModel).where(
                IntelligenceReportModel.version_id == version_id
            )
        )
        model = result.scalar_one_or_none()
        return to_intelligence_report(model) if model else None

    async def get_by_dataset(
        self, *, dataset_id: UUID, organization_id: UUID, version_id: UUID | None = None
    ) -> IntelligenceReport | None:
        query = select(IntelligenceReportModel).where(
            IntelligenceReportModel.dataset_id == dataset_id,
            IntelligenceReportModel.organization_id == organization_id,
        )
        if version_id is not None:
            query = query.where(IntelligenceReportModel.version_id == version_id)
        result = await self._session.execute(query.order_by(IntelligenceReportModel.created_at.desc()))
        model = result.scalars().first()
        return to_intelligence_report(model) if model else None

    async def upsert(self, report: IntelligenceReport) -> IntelligenceReport:
        result = await self._session.execute(
            select(IntelligenceReportModel).where(
                IntelligenceReportModel.version_id == report.version_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            model = IntelligenceReportModel(
                id=report.id,
                dataset_id=report.dataset_id,
                version_id=report.version_id,
                organization_id=report.organization_id,
                status=report.status.value,
                quality_score=report.quality_score,
                health_score=report.health_score,
                rows_sampled=report.rows_sampled,
                total_rows=report.total_rows,
                report_json=report.report,
                error_message=report.error_message,
                computed_at=report.computed_at,
            )
            self._session.add(model)
        else:
            existing.status = report.status.value
            existing.quality_score = report.quality_score
            existing.health_score = report.health_score
            existing.rows_sampled = report.rows_sampled
            existing.total_rows = report.total_rows
            existing.report_json = report.report
            existing.error_message = report.error_message
            existing.computed_at = report.computed_at
            model = existing
        await self._session.flush()
        return to_intelligence_report(model)

    async def delete_for_version(self, *, version_id: UUID) -> None:
        result = await self._session.execute(
            select(IntelligenceReportModel).where(
                IntelligenceReportModel.version_id == version_id
            )
        )
        model = result.scalar_one_or_none()
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
