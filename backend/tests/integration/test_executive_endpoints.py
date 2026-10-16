"""Integration tests for executive intelligence endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_executive_report_after_decision(dataset_client: AsyncClient) -> None:
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
        files={"file": ("executive.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    dag_resp = await dataset_client.post(
        "/api/v1/causal/dag",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "name": "Executive DAG",
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
            "name": "Executive simulation",
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
            "name": "Executive decision",
            "primary_objective": "maximize_revenue",
            "simulation_run_ids": [simulation_id],
            "risk_tolerance": 0.8,
            "min_confidence": 0.3,
            "max_budget": 10000,
        },
    )
    assert decision.status_code == 201, decision.text
    decision_id = decision.json()["data"]["id"]

    report_resp = await dataset_client.post(
        "/api/v1/reports/generate",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "decision_run_id": decision_id,
            "name": "Q3 Executive Brief",
            "business_objective": "Maximize revenue from treatment uplift",
            "include_technical_appendix": True,
        },
    )
    assert report_resp.status_code == 201, report_resp.text
    report_body = report_resp.json()["data"]
    assert report_body["status"] == "completed"
    assert "executive_summary" in report_body["result"]
    assert "explainability" in report_body["result"]
    report_id = report_body["id"]

    get_resp = await dataset_client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["name"] == "Q3 Executive Brief"

    list_resp = await dataset_client.get(
        "/api/v1/reports",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    export_resp = await dataset_client.post(
        "/api/v1/reports/export",
        headers=headers,
        params={"report_id": report_id},
        json={"format": "markdown"},
    )
    assert export_resp.status_code == 200
    export_data = export_resp.json()["data"]
    assert "content" in export_data
    assert "Executive Summary" in export_data["content"]

    dashboard = await dataset_client.get(
        "/api/v1/executive/dashboard",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert dashboard.status_code == 200
    dash = dashboard.json()["data"]
    assert "business_health_score" in dash
    assert "recommendation_status" in dash
