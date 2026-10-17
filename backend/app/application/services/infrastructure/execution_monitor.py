"""Execution monitoring and job snapshots."""

from __future__ import annotations

from app.application.dto.infrastructure import JobSnapshotDTO
from app.domain.entities.analytics_job import AnalyticsJob


class ExecutionMonitor:
    """Transform jobs into monitor-friendly snapshots."""

    def snapshot(self, job: AnalyticsJob) -> JobSnapshotDTO:
        duration_ms = None
        if job.started_at and job.completed_at:
            duration_ms = int((job.completed_at - job.started_at).total_seconds() * 1000)
        elif job.started_at:
            from app.shared.utils.datetime import utc_now

            duration_ms = int((utc_now() - job.started_at).total_seconds() * 1000)

        return JobSnapshotDTO(
            id=str(job.id),
            job_type=job.job_type.value,
            status=job.status.value,
            name=job.name,
            progress=job.progress,
            error_message=job.error_message,
            retry_count=job.retry_count,
            logs=job.logs,
            queued_at=job.queued_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            estimated_duration_ms=job.estimated_duration_ms,
            duration_ms=duration_ms,
        )
