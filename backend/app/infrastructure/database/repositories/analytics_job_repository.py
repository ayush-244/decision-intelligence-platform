"""SQLAlchemy analytics job repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.analytics_job import AnalyticsJob
from app.domain.repositories.analytics_job_repository import AnalyticsJobRepository
from app.domain.value_objects.infrastructure import JobStatus, JobType
from app.infrastructure.database.mappers.analytics_job import to_analytics_job
from app.infrastructure.database.models.analytics_job import AnalyticsJobModel


class SqlAlchemyAnalyticsJobRepository(AnalyticsJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: AnalyticsJob) -> AnalyticsJob:
        model = AnalyticsJobModel(
            id=job.id,
            organization_id=job.organization_id,
            created_by=job.created_by,
            job_type=job.job_type.value,
            status=job.status.value,
            dataset_id=job.dataset_id,
            version_id=job.version_id,
            resource_type=job.resource_type,
            resource_id=job.resource_id,
            name=job.name,
            configuration_json=job.configuration,
            result_json=job.result,
            progress=job.progress,
            error_message=job.error_message,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
            logs_json=list(job.logs),
            estimated_duration_ms=job.estimated_duration_ms,
            queued_at=job.queued_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        self._session.add(model)
        await self._session.flush()
        return to_analytics_job(model)

    async def update(self, job: AnalyticsJob) -> AnalyticsJob:
        result = await self._session.execute(
            select(AnalyticsJobModel).where(AnalyticsJobModel.id == job.id)
        )
        model = result.scalar_one()
        model.status = job.status.value
        model.configuration_json = job.configuration
        model.result_json = job.result
        model.progress = job.progress
        model.error_message = job.error_message
        model.retry_count = job.retry_count
        model.logs_json = list(job.logs)
        model.estimated_duration_ms = job.estimated_duration_ms
        model.started_at = job.started_at
        model.completed_at = job.completed_at
        await self._session.flush()
        return to_analytics_job(model)

    async def get_by_id(
        self, *, job_id: UUID, organization_id: UUID
    ) -> AnalyticsJob | None:
        result = await self._session.execute(
            select(AnalyticsJobModel).where(
                AnalyticsJobModel.id == job_id,
                AnalyticsJobModel.organization_id == organization_id,
            )
        )
        model = result.scalar_one_or_none()
        return to_analytics_job(model) if model else None

    async def get_by_id_any(self, *, job_id: UUID) -> AnalyticsJob | None:
        result = await self._session.execute(
            select(AnalyticsJobModel).where(AnalyticsJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return to_analytics_job(model) if model else None

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        status: JobStatus | None = None,
        job_type: JobType | None = None,
        limit: int = 50,
    ) -> list[AnalyticsJob]:
        stmt = (
            select(AnalyticsJobModel)
            .where(AnalyticsJobModel.organization_id == organization_id)
            .order_by(AnalyticsJobModel.queued_at.desc())
            .limit(limit)
        )
        if status is not None:
            stmt = stmt.where(AnalyticsJobModel.status == status.value)
        if job_type is not None:
            stmt = stmt.where(AnalyticsJobModel.job_type == job_type.value)
        result = await self._session.execute(stmt)
        return [to_analytics_job(m) for m in result.scalars()]

    async def list_running(self, *, limit: int = 20) -> list[AnalyticsJob]:
        result = await self._session.execute(
            select(AnalyticsJobModel)
            .where(AnalyticsJobModel.status == JobStatus.RUNNING.value)
            .order_by(AnalyticsJobModel.started_at.desc())
            .limit(limit)
        )
        return [to_analytics_job(m) for m in result.scalars()]
