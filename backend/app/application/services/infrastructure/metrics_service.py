"""Metrics collection — OpenTelemetry-compatible foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from app.application.dto.infrastructure import InfrastructureMetricsDTO
from app.application.services.infrastructure.cache_service import AnalyticsCacheService
from app.domain.ports.job_queue import JobQueuePort
from app.domain.repositories.analytics_job_repository import AnalyticsJobRepository
from app.domain.value_objects.infrastructure import JobStatus


@dataclass
class MetricsCollector:
    """In-process metrics registry with slow-query detection."""

    slow_query_threshold_ms: float = 500.0
    slow_queries_detected: int = 0
    request_durations_ms: list[float] = field(default_factory=list)

    def record_duration(self, *, name: str, duration_ms: float) -> None:
        self.request_durations_ms.append(duration_ms)
        if duration_ms >= self.slow_query_threshold_ms:
            self.slow_queries_detected += 1

    def time_block(self, name: str) -> "_Timer":
        return _Timer(self, name)


class _Timer:
    def __init__(self, collector: MetricsCollector, name: str) -> None:
        self._collector = collector
        self._name = name
        self._start = perf_counter()

    def __enter__(self) -> _Timer:
        return self

    def __exit__(self, *args: Any) -> None:
        elapsed = (perf_counter() - self._start) * 1000
        self._collector.record_duration(name=self._name, duration_ms=elapsed)


# Process-wide singleton for infrastructure metrics
metrics_collector = MetricsCollector()


class InfrastructureMetricsService:
    def __init__(
        self,
        jobs: AnalyticsJobRepository,
        queue: JobQueuePort,
        cache: AnalyticsCacheService,
        collector: MetricsCollector,
    ) -> None:
        self._jobs = jobs
        self._queue = queue
        self._cache = cache
        self._collector = collector

    async def snapshot(self, *, organization_id: Any = None) -> InfrastructureMetricsDTO:
        queue_depth = await self._queue.queue_depth()
        running = await self._jobs.list_running(limit=100)
        # Aggregate counts — org-scoped when provided
        queued = 0
        completed = 0
        failed = 0
        durations: list[float] = []
        if organization_id is not None:
            from uuid import UUID

            org_id = organization_id if isinstance(organization_id, UUID) else UUID(str(organization_id))
            for status in (JobStatus.QUEUED, JobStatus.COMPLETED, JobStatus.FAILED):
                rows = await self._jobs.list_for_organization(
                    organization_id=org_id, status=status, limit=200
                )
                if status is JobStatus.QUEUED:
                    queued = len(rows)
                elif status is JobStatus.COMPLETED:
                    completed = len(rows)
                    for j in rows:
                        if j.started_at and j.completed_at:
                            durations.append(
                                (j.completed_at - j.started_at).total_seconds() * 1000
                            )
                else:
                    failed = len(rows)

        cache_stats = await self._cache.stats()
        avg_duration = sum(durations) / len(durations) if durations else None

        return InfrastructureMetricsDTO(
            queue_depth=queue_depth,
            jobs_queued=queued,
            jobs_running=len(running),
            jobs_completed_24h=completed,
            jobs_failed_24h=failed,
            cache_hits=int(cache_stats.get("hits", 0)),
            cache_misses=int(cache_stats.get("misses", 0)),
            cache_keys=int(cache_stats.get("keys", 0)),
            avg_job_duration_ms=avg_duration,
            slow_queries_detected=self._collector.slow_queries_detected,
        )
