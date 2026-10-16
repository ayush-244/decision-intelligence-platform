"""Integration tests for dataset ingestion endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

_SAMPLE_CSV = b"id,name,value\n1,alpha,10\n2,beta,20\n"


async def _bootstrap_project(client: AsyncClient) -> tuple[str, str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "data@example.com",
            "password": "Password1",
            "full_name": "Data Owner",
        },
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "data@example.com", "password": "Password1"},
    )
    assert login.status_code == 200
    access_token = login.json()["data"]["tokens"]["access_token"]

    org = await client.post(
        "/api/v1/organizations",
        json={"name": "Data Org"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    org_id = org.json()["data"]["id"]

    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    workspace = await client.post(
        "/api/v1/workspaces",
        json={"organization_id": org_id, "name": "Lab"},
        headers=headers,
    )
    workspace_id = workspace.json()["data"]["id"]

    project = await client.post(
        "/api/v1/projects",
        json={"workspace_id": workspace_id, "name": "Experiments"},
        headers=headers,
    )
    project_id = project.json()["data"]["id"]
    return access_token, org_id, project_id


@pytest.mark.asyncio
async def test_dataset_upload_list_preview_and_version(dataset_client: AsyncClient) -> None:
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id, "name": "Sales"},
        files={"file": ("sales.csv", _SAMPLE_CSV, "text/csv")},
    )
    assert upload.status_code == 201
    body = upload.json()["data"]
    dataset_id = body["dataset"]["id"]
    assert body["version"]["version_number"] == 1
    assert body["version"]["row_count"] == 2
    assert body["version"]["column_count"] == 3
    assert body["validation"]["status"] == "passed"

    listed = await dataset_client.get(
        f"/api/v1/datasets?project_id={project_id}",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    preview = await dataset_client.get(
        f"/api/v1/datasets/{dataset_id}/preview",
        headers=headers,
    )
    assert preview.status_code == 200
    preview_body = preview.json()["data"]
    assert len(preview_body["rows"]) == 2
    assert len(preview_body["columns"]) == 3

    new_version = await dataset_client.post(
        f"/api/v1/datasets/{dataset_id}/new-version",
        headers=headers,
        files={"file": ("sales_v2.csv", _SAMPLE_CSV + b"3,gamma,30\n", "text/csv")},
    )
    assert new_version.status_code == 201
    assert new_version.json()["data"]["version"]["version_number"] == 2

    versions = await dataset_client.get(
        f"/api/v1/datasets/{dataset_id}/versions",
        headers=headers,
    )
    assert versions.status_code == 200
    assert len(versions.json()["data"]) == 2


@pytest.mark.asyncio
async def test_dataset_intelligence_analyze_and_summary(dataset_client: AsyncClient) -> None:
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id, "name": "Intel"},
        files={"file": ("intel.csv", _SAMPLE_CSV, "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    analyze = await dataset_client.post(
        f"/api/v1/datasets/{dataset_id}/intelligence/analyze",
        headers=headers,
    )
    assert analyze.status_code == 201
    assert analyze.json()["data"]["quality_score"] is not None

    summary = await dataset_client.get(
        f"/api/v1/datasets/{dataset_id}/summary",
        headers=headers,
    )
    assert summary.status_code == 200
    assert summary.json()["data"]["quality_score"] is not None

    intelligence = await dataset_client.get(
        f"/api/v1/datasets/{dataset_id}/intelligence",
        headers=headers,
    )
    assert intelligence.status_code == 200
    body = intelligence.json()["data"]
    assert "columns" in body
    assert "data_quality" in body


@pytest.mark.asyncio
async def test_dataset_upload_requires_auth(dataset_client: AsyncClient) -> None:
    response = await dataset_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": "00000000-0000-0000-0000-000000000001"},
        files={"file": ("x.csv", _SAMPLE_CSV, "text/csv")},
    )
    assert response.status_code == 401
