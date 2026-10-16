"""Integration tests for infrastructure and job endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.application.services.infrastructure.worker import BackgroundWorker
from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_submit_list_and_process_job(dataset_client: AsyncClient) -> None:
    access_token, org_id, _project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    submit = await dataset_client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "job_type": "statistics",
            "name": "Nightly statistics",
            "configuration": {"mode": "full"},
        },
    )
    assert submit.status_code == 202, submit.text
    job_id = submit.json()["data"]["id"]
    assert submit.json()["data"]["status"] == "queued"

    listed = await dataset_client.get("/api/v1/jobs", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == job_id for item in listed.json()["data"])

    detail = await dataset_client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["name"] == "Nightly statistics"

    from uuid import UUID

    from app.presentation.api import deps

    app = dataset_client._transport.app  # type: ignore[attr-defined]
    queue = app.state.job_queue
    job_repo = app.dependency_overrides[deps.get_analytics_job_repository]()

    async def run_with_repo(operation):
        return await operation(job_repo)

    worker = BackgroundWorker(run_with_repo, queue)
    job = await job_repo.get_by_id_any(job_id=UUID(job_id))
    assert job is not None
    completed = await worker.process_job(job)
    assert completed.status.value == "completed"

    metrics = await dataset_client.get("/api/v1/infrastructure/metrics", headers=headers)
    assert metrics.status_code == 200
    body = metrics.json()["data"]
    assert "queue_depth" in body
    assert "cache_hits" in body

    cache_stats = await dataset_client.get("/api/v1/infrastructure/cache/stats", headers=headers)
    assert cache_stats.status_code == 200

    queue_status = await dataset_client.get("/api/v1/infrastructure/queue", headers=headers)
    assert queue_status.status_code == 200
