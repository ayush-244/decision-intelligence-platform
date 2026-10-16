"""Integration tests for simulation API endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_simulation_run_with_causal_model(dataset_client: AsyncClient) -> None:
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
        files={"file": ("sim.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    dag_resp = await dataset_client.post(
        "/api/v1/causal/dag",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "name": "Sim DAG",
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
    assert analyze.status_code == 201, analyze.text
    causal_id = analyze.json()["data"]["id"]

    scenario = await dataset_client.post(
        "/api/v1/scenarios",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "name": "Increase treatment 20%",
            "objective": "Improve outcome",
            "interventions": [
                {"variable": "treatment", "mode": "relative", "value": 0.2, "reason": "Pilot"}
            ],
            "constraints": [
                {
                    "type": "max_budget",
                    "severity": "hard",
                    "threshold": 10000,
                    "description": "Budget cap",
                }
            ],
        },
    )
    assert scenario.status_code == 201, scenario.text
    scenario_id = scenario.json()["data"]["id"]

    sim = await dataset_client.post(
        "/api/v1/simulations",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "causal_analysis_id": causal_id,
            "scenario_id": scenario_id,
            "name": "Treatment uplift simulation",
            "objective": "Estimate outcome if treatment increases 20%",
            "monte_carlo_iterations": 200,
            "roi_assumptions": {
                "revenue_per_outcome_unit": 100,
                "intervention_cost": 500,
            },
        },
    )
    assert sim.status_code == 201, sim.text
    body = sim.json()["data"]
    assert body["status"] == "completed"
    assert "counterfactual" in body["result"]
    assert "monte_carlo" in body["result"]
    assert "risk" in body["result"]
    assert "roi" in body["result"]
    assert "interpretation" in body["result"]

    history = await dataset_client.get(
        "/api/v1/simulations/history",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert history.status_code == 200
    assert len(history.json()["data"]) >= 1

    scenarios = await dataset_client.get(
        "/api/v1/scenarios",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert scenarios.status_code == 200
    assert len(scenarios.json()["data"]) >= 1
