"""Background worker — dequeue and execute jobs."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any, TypeVar

from app.core.logging import get_logger
from app.domain.entities.analytics_job import AnalyticsJob
from app.domain.ports.job_queue import JobQueuePort
from app.domain.repositories.analytics_job_repository import AnalyticsJobRepository
from app.domain.value_objects.infrastructure import JobStatus, JobType
from app.shared.utils.datetime import utc_now

_logger = get_logger(__name__)

JobHandler = Callable[[AnalyticsJob, AnalyticsJobRepository], Awaitable[dict[str, Any]]]
T = TypeVar("T")
RepoOperation = Callable[[AnalyticsJobRepository], Awaitable[T]]


class BackgroundWorker:
    """Poll queue and execute registered handlers."""

    def __init__(
        self,
        run_with_repo: Callable[[RepoOperation[T]], Awaitable[T]],
        queue: JobQueuePort,
        handlers: dict[JobType, JobHandler] | None = None,
    ) -> None:
        self._run_with_repo = run_with_repo
        self._queue = queue
        self._handlers = handlers or {}
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def register(self, job_type: JobType, handler: JobHandler) -> None:
        self._handlers[job_type] = handler

    async def start(self, *, poll_interval: float = 1.0) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(poll_interval))
        _logger.info("background_worker_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        _logger.info("background_worker_stopped")

    async def process_job(self, job: AnalyticsJob) -> AnalyticsJob:
        return await self._run_with_repo(lambda jobs: self._execute(jobs, job))

    async def _loop(self, poll_interval: float) -> None:
        while self._running:
            job_id = await self._queue.dequeue(timeout_seconds=poll_interval)
            if job_id is None:
                continue
            try:

                async def _process(jobs: AnalyticsJobRepository) -> None:
                    job = await jobs.get_by_id_any(job_id=job_id)
                    if job is not None and job.status in {
                        JobStatus.QUEUED,
                        JobStatus.RETRYING,
                    }:
                        await self._execute(jobs, job)

                await self._run_with_repo(_process)
            except Exception:  # noqa: BLE001
                _logger.exception("worker_job_error", job_id=str(job_id))

    async def _execute(self, jobs: AnalyticsJobRepository, job: AnalyticsJob) -> AnalyticsJob:
        now = utc_now()
        running = replace(
            job,
            status=JobStatus.RUNNING,
            started_at=now,
            progress=5,
            logs=job.logs + (f"Started at {now.isoformat()}",),
            updated_at=now,
        )
        await jobs.update(running)

        handler = self._handlers.get(job.job_type, self._default_handler)
        try:
            result = await handler(running, jobs)
            done = replace(
                running,
                status=JobStatus.COMPLETED,
                progress=100,
                result=result,
                completed_at=utc_now(),
                logs=running.logs + ("Completed successfully.",),
                updated_at=utc_now(),
            )
            return await jobs.update(done)
        except Exception as exc:  # noqa: BLE001
            failed = replace(
                running,
                status=JobStatus.FAILED,
                error_message=str(exc),
                completed_at=utc_now(),
                logs=running.logs + (f"Failed: {exc}",),
                updated_at=utc_now(),
            )
            return await jobs.update(failed)

    async def _default_handler(
        self, job: AnalyticsJob, jobs: AnalyticsJobRepository
    ) -> dict[str, Any]:
        steps = 5
        current = job
        for i in range(1, steps + 1):
            await asyncio.sleep(0.02)
            progress = int(i / steps * 95)
            current = replace(
                current,
                progress=progress,
                logs=current.logs + (f"Progress {progress}%",),
                updated_at=utc_now(),
            )
            current = await jobs.update(current)
        return {
            "job_type": current.job_type.value,
            "message": "Infrastructure worker completed job.",
            "resource_id": str(current.resource_id) if current.resource_id else None,
        }
