"""Integration tests for decision intelligence endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_decision_analyze_after_simulation(dataset_client: AsyncClient) -> None:
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
        files={"file": ("decision.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    dag_resp = await dataset_client.post(
        "/api/v1/causal/dag",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "name": "Decision DAG",
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
    causal_id = analyze.json()["data"]["id"]

    sim = await dataset_client.post(
        "/api/v1/simulations",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "causal_analysis_id": causal_id,
            "name": "Uplift simulation",
            "objective": "Increase outcome",
            "interventions": [{"variable": "treatment", "mode": "relative", "value": 0.2}],
            "monte_carlo_iterations": 200,
            "roi_assumptions": {"revenue_per_outcome_unit": 100, "intervention_cost": 50},
        },
    )
    assert sim.status_code == 201, sim.text
    simulation_id = sim.json()["data"]["id"]

    decision = await dataset_client.post(
        "/api/v1/decisions/analyze",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "name": "Revenue optimization",
            "primary_objective": "maximize_revenue",
            "simulation_run_ids": [simulation_id],
            "risk_tolerance": 0.8,
            "min_confidence": 0.3,
            "max_budget": 10000,
        },
    )
    assert decision.status_code == 201, decision.text
    body = decision.json()["data"]
    assert body["status"] == "completed"
    assert "recommendations" in body["result"]
    assert len(body["result"]["recommendations"]) >= 1

    decision_id = body["id"]
    recs = await dataset_client.get(
        "/api/v1/recommendations",
        headers=headers,
        params={"decision_id": decision_id},
    )
    assert recs.status_code == 200
    assert len(recs.json()["data"]) >= 1

    tradeoffs = await dataset_client.get(
        "/api/v1/tradeoffs",
        headers=headers,
        params={"decision_id": decision_id},
    )
    assert tradeoffs.status_code == 200

    priorities = await dataset_client.get(
        "/api/v1/priorities",
        headers=headers,
        params={"decision_id": decision_id},
    )
    assert priorities.status_code == 200
    assert len(priorities.json()["data"]) >= 1

    objectives = await dataset_client.get("/api/v1/objectives", headers=headers)
    assert objectives.status_code == 200
    assert len(objectives.json()["data"]) >= 1

    history = await dataset_client.get(
        "/api/v1/decisions",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert history.status_code == 200
    assert len(history.json()["data"]) >= 1
