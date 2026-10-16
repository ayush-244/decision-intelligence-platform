"""Integration tests for causal API endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_causal_analyze_with_dag(dataset_client: AsyncClient) -> None:
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    csv_content = (
        "treatment,outcome,confounder\n"
        "0,10,1\n0,11,1\n0,9,1\n0,10,2\n"
        "1,15,1\n1,16,2\n1,14,2\n1,17,2\n"
    )
    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files={"file": ("causal.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    dag_resp = await dataset_client.post(
        "/api/v1/causal/dag",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "name": "Test DAG",
            "nodes": [
                {"id": "confounder", "label": "confounder", "role": "confounder"},
                {"id": "treatment", "label": "treatment", "role": "treatment"},
                {"id": "outcome", "label": "outcome", "role": "outcome"},
            ],
            "edges": [
                {"source": "confounder", "target": "treatment"},
                {"source": "confounder", "target": "outcome"},
                {"source": "treatment", "target": "outcome"},
            ],
            "variable_roles": {
                "confounder": "confounder",
                "treatment": "treatment",
                "outcome": "outcome",
            },
        },
    )
    assert dag_resp.status_code == 201, dag_resp.text
    dag_id = dag_resp.json()["data"]["id"]

    analyze = await dataset_client.post(
        "/api/v1/causal/analyze",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "dag_id": dag_id,
            "treatment": "treatment",
            "outcome": "outcome",
            "business_question": "Does treatment increase outcome?",
        },
    )
    assert analyze.status_code == 201, analyze.text
    body = analyze.json()["data"]
    assert body["status"] == "completed"
    assert "result" in body
    assert "interpretation" in body["result"]
    assert "treatment_effect" in body["result"]

    history = await dataset_client.get(
        "/api/v1/causal/history",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert history.status_code == 200
    assert len(history.json()["data"]) >= 1
