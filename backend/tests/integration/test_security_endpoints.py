"""Integration tests for security middleware and governance APIs."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_security_headers_on_liveness(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"


@pytest.mark.asyncio
async def test_trace_id_header_echoed(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Trace-ID": "abc123trace"})
    assert response.headers.get("x-trace-id") == "abc123trace"


@pytest.mark.asyncio
async def test_governance_error_catalog(client: AsyncClient) -> None:
    response = await client.get("/api/v1/governance/errors")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()["data"]}
    assert "rate_limit_exceeded" in codes
    assert "forbidden" in codes


@pytest.mark.asyncio
async def test_forbidden_without_organization(dataset_client: AsyncClient) -> None:
    await dataset_client.post(
        "/api/v1/auth/register",
        json={"email": "sec@example.com", "password": "Password1", "full_name": "Sec User"},
    )
    login = await dataset_client.post(
        "/api/v1/auth/login",
        json={"email": "sec@example.com", "password": "Password1"},
    )
    token = login.json()["data"]["tokens"]["access_token"]
    response = await dataset_client.get(
        "/api/v1/infrastructure/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in {400, 403, 422}


@pytest.mark.asyncio
async def test_viewer_cannot_invalidate_cache(dataset_client: AsyncClient) -> None:
    """Authorization enforcement returns forbidden for insufficient role."""
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    owner_headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=owner_headers,
        data={"project_id": project_id},
        files={"file": ("sec.csv", b"id,v\n1,2\n", "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    await dataset_client.post(
        "/api/v1/auth/register",
        json={"email": "viewer@example.com", "password": "Password1", "full_name": "Viewer"},
    )
    viewer_login = await dataset_client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@example.com", "password": "Password1"},
    )
    viewer_token = viewer_login.json()["data"]["tokens"]["access_token"]

    invalidate = await dataset_client.post(
        "/api/v1/infrastructure/cache/invalidate",
        headers={
            "Authorization": f"Bearer {viewer_token}",
            "X-Organization-ID": org_id,
        },
        json={"dataset_id": dataset_id},
    )
    assert invalidate.status_code == 403
    body = invalidate.json()
    assert body["error"]["code"] == "forbidden"
