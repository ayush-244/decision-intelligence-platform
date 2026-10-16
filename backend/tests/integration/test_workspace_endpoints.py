"""Integration tests for unified workspace endpoints."""

from __future__ import annotations

import io
from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_workspace_session_search_timeline(dataset_client: AsyncClient) -> None:
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    csv_content = "treatment,outcome\n0,10\n1,15\n"
    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files={"file": ("workspace.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    create = await dataset_client.post(
        "/api/v1/sessions",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "name": f"Q3 Revenue Decision {uuid4().hex[:6]}",
            "description": "Unified workspace session",
        },
    )
    assert create.status_code == 201, create.text
    session_id = create.json()["data"]["id"]

    get_resp = await dataset_client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    assert get_resp.status_code == 200
    body = get_resp.json()["data"]
    assert "progress" in body
    assert body["progress"]["percent_complete"] > 0

    patch = await dataset_client.patch(
        f"/api/v1/sessions/{session_id}",
        headers=headers,
        json={"current_step": "statistical_analysis"},
    )
    assert patch.status_code == 200

    timeline = await dataset_client.get(
        f"/api/v1/sessions/{session_id}/timeline", headers=headers
    )
    assert timeline.status_code == 200
    assert len(timeline.json()["data"]) >= 1

    comment = await dataset_client.post(
        f"/api/v1/sessions/{session_id}/comments",
        headers=headers,
        json={"body": "Review assumptions before causal step.", "mentions": []},
    )
    assert comment.status_code == 201

    search = await dataset_client.get(
        "/api/v1/workspace/search",
        headers=headers,
        params={"q": "revenue", "dataset_id": dataset_id},
    )
    assert search.status_code == 200
    assert len(search.json()["data"]) >= 1

    list_resp = await dataset_client.get(
        "/api/v1/sessions",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    activity = await dataset_client.get("/api/v1/workspace/activity", headers=headers)
    assert activity.status_code == 200

    session_b = await dataset_client.post(
        "/api/v1/sessions",
        headers=headers,
        json={"dataset_id": dataset_id, "name": "Q3 Alternative"},
    )
    session_b_id = session_b.json()["data"]["id"]

    compare = await dataset_client.post(
        "/api/v1/workspace/compare",
        headers=headers,
        json={"session_a_id": session_id, "session_b_id": session_b_id},
    )
    assert compare.status_code == 200
    assert "items" in compare.json()["data"]
