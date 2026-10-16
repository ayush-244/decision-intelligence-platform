"""Integration tests for statistics API endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_statistics_analyze_independent_ttest(dataset_client: AsyncClient) -> None:
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    csv_content = (
        "value,group\n"
        "10.1,A\n10.2,A\n9.8,A\n9.9,A\n10.0,A\n"
        "12.1,B\n12.3,B\n11.9,B\n12.0,B\n12.2,B\n"
    )
    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files={"file": ("groups.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert upload.status_code == 201
    dataset_id = upload.json()["data"]["dataset"]["id"]

    analyze = await dataset_client.post(
        "/api/v1/statistics/analyze",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "goal": "compare_groups",
            "research_question": "Do groups A and B differ in value?",
            "variables": [
                {"name": "value", "role": "outcome"},
                {"name": "group", "role": "grouping"},
            ],
        },
    )
    assert analyze.status_code == 201, analyze.text
    body = analyze.json()["data"]
    assert body["status"] == "completed"
    assert body["test_type"] in {"independent_ttest", "welch_ttest", "mann_whitney_u"}
    assert "result" in body
    assert "interpretation" in body["result"]
    assert "effect_sizes" in body["result"]

    analysis_id = body["id"]
    get_resp = await dataset_client.get(
        f"/api/v1/statistics/{analysis_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200

    history = await dataset_client.get(
        "/api/v1/statistics/history",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert history.status_code == 200
    assert len(history.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_statistics_recommendations(dataset_client: AsyncClient) -> None:
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    csv_content = "x,y\n1,2\n2,4\n3,5\n4,4\n5,6\n"
    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files={"file": ("corr.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    rec = await dataset_client.post(
        "/api/v1/statistics/recommendations",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "goal": "association",
            "variables": [
                {"name": "x", "role": "predictor"},
                {"name": "y", "role": "outcome"},
            ],
        },
    )
    assert rec.status_code == 200
    data = rec.json()["data"]
    assert data["recommended_test"] == "pearson_correlation"
    assert data["reasoning"]
