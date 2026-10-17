"""Analytics job ORM ↔ domain mapper."""

from __future__ import annotations

from app.domain.entities.analytics_job import AnalyticsJob
from app.domain.value_objects.infrastructure import JobStatus, JobType
from app.infrastructure.database.models.analytics_job import AnalyticsJobModel


def to_analytics_job(model: AnalyticsJobModel) -> AnalyticsJob:
    return AnalyticsJob(
        id=model.id,
        organization_id=model.organization_id,
        created_by=model.created_by,
        job_type=JobType(model.job_type),
        status=JobStatus(model.status),
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        resource_type=model.resource_type,
        resource_id=model.resource_id,
        name=model.name,
        configuration=model.configuration_json,
        result=model.result_json,
        progress=model.progress,
        error_message=model.error_message,
        retry_count=model.retry_count,
        max_retries=model.max_retries,
        logs=tuple(model.logs_json or ()),
        estimated_duration_ms=model.estimated_duration_ms,
        queued_at=model.queued_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
