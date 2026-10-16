"""Unit tests for enterprise infrastructure services."""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest

from app.application.dto.infrastructure import SubmitJobRequestDTO
from app.application.services.infrastructure.cache_service import AnalyticsCacheService
from app.application.services.infrastructure.job_orchestrator import JobOrchestrator
from app.application.services.infrastructure.worker import BackgroundWorker
from app.domain.value_objects.infrastructure import CacheNamespace, JobStatus, JobType
from app.infrastructure.cache.in_memory_cache_store import InMemoryCacheStore
from app.infrastructure.queue.in_memory_job_queue import InMemoryJobQueue
from app.shared.utils.datetime import utc_now
from tests.infrastructure_fakes import InMemoryInfrastructureStore


@pytest.mark.asyncio
async def test_cache_version_aware_keys_and_invalidation() -> None:
    store = InMemoryCacheStore()
    cache = AnalyticsCacheService(store)
    key = cache.build_key(
        namespace=CacheNamespace.ANALYSIS,
        organization_id="org-1",
        dataset_id="ds-1",
        version_id="v1",
        suffix="summary",
    )
    await cache.set_json(key=key, value={"score": 0.9}, namespace=CacheNamespace.ANALYSIS)
    assert await cache.get_json(key) == {"score": 0.9}
    deleted = await cache.invalidate_dataset(
        organization_id="org-1", dataset_id="ds-1", version_id="v1"
    )
    assert deleted >= 1
    assert await cache.get_json(key) is None


@pytest.mark.asyncio
async def test_job_orchestrator_submit_cancel_retry() -> None:
    infra = InMemoryInfrastructureStore()
    orchestrator = JobOrchestrator(infra.job_repo(), infra.queue)
    org_id = uuid4()
    job = await orchestrator.submit(
        organization_id=org_id,
        created_by=None,
        request=SubmitJobRequestDTO(
            job_type=JobType.STATISTICS.value,
            name="Test stats job",
            dataset_id=None,
            version_id=None,
            resource_type=None,
            resource_id=None,
            configuration={},
        ),
    )
    assert job.status is JobStatus.QUEUED
    assert await infra.queue.queue_depth() == 1

    cancelled = await orchestrator.cancel(job=job)
    assert cancelled.status is JobStatus.CANCELLED

    failed_job = await orchestrator.submit(
        organization_id=org_id,
        created_by=None,
        request=SubmitJobRequestDTO(
            job_type=JobType.SIMULATION.value,
            name="Retry me",
            dataset_id=None,
            version_id=None,
            resource_type=None,
            resource_id=None,
            configuration={},
        ),
    )
    from dataclasses import replace

    failed = replace(
        failed_job,
        status=JobStatus.FAILED,
        error_message="boom",
        completed_at=utc_now(),
    )
    await infra.job_repo().update(failed)
    retried = await orchestrator.retry(job=failed)
    assert retried.status is JobStatus.RETRYING
    assert retried.retry_count == 1


@pytest.mark.asyncio
async def test_background_worker_processes_queue() -> None:
    infra = InMemoryInfrastructureStore()
    orchestrator = JobOrchestrator(infra.job_repo(), infra.queue)

    async def run_with_repo(operation):
        return await operation(infra.job_repo())

    worker = BackgroundWorker(run_with_repo, infra.queue)
    org_id = uuid4()
    job = await orchestrator.submit(
        organization_id=org_id,
        created_by=None,
        request=SubmitJobRequestDTO(
            job_type=JobType.DATA_INTELLIGENCE.value,
            name="Worker job",
            dataset_id=None,
            version_id=None,
            resource_type=None,
            resource_id=None,
            configuration={},
        ),
    )
    dequeued = await infra.queue.dequeue(timeout_seconds=0.01)
    assert dequeued == job.id
    await infra.queue.enqueue(job_id=job.id)
    completed = await worker.process_job(job)
    assert completed.status is JobStatus.COMPLETED
    assert completed.progress == 100


@pytest.mark.asyncio
async def test_in_memory_queue_concurrency() -> None:
    queue = InMemoryJobQueue()
    ids = [uuid4() for _ in range(20)]

    async def producer() -> None:
        for job_id in ids:
            await queue.enqueue(job_id=job_id)

    async def consumer(results: list) -> None:
        for _ in ids:
            item = await queue.dequeue(timeout_seconds=1.0)
            if item is not None:
                results.append(item)

    collected: list = []
    await asyncio.gather(producer(), consumer(collected))
    assert len(collected) == len(ids)
