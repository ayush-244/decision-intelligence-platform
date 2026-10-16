"""Integration tests for AI Decision Copilot endpoints."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient

from tests.integration.test_dataset_endpoints import _bootstrap_project


@pytest.mark.asyncio
async def test_copilot_conversation_lifecycle(dataset_client: AsyncClient) -> None:
    access_token, org_id, project_id = await _bootstrap_project(dataset_client)
    headers = {"Authorization": f"Bearer {access_token}", "X-Organization-ID": org_id}

    csv_content = "treatment,outcome\n0,10\n1,15\n"
    upload = await dataset_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files={"file": ("copilot.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    dataset_id = upload.json()["data"]["dataset"]["id"]

    create = await dataset_client.post(
        "/api/v1/copilot/conversations",
        headers=headers,
        json={"title": "Revenue analysis", "dataset_id": dataset_id},
    )
    assert create.status_code == 201, create.text
    conv = create.json()["data"]
    assert conv["title"] == "Revenue analysis"
    assert len(conv["suggested_questions"]) >= 1
    conversation_id = conv["id"]

    context = await dataset_client.get(
        "/api/v1/copilot/context",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert context.status_code == 200
    assert "prompt_preview" in context.json()["data"]

    message = await dataset_client.post(
        f"/api/v1/copilot/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "What can you help me understand about this dataset?"},
    )
    assert message.status_code == 200, message.text
    body = message.json()["data"]
    assert len(body["messages"]) >= 2
    assistant = [m for m in body["messages"] if m["role"] == "assistant"][0]
    assert assistant["content"]
    assert isinstance(assistant["citations"], list)

    listed = await dataset_client.get(
        "/api/v1/copilot/conversations",
        headers=headers,
        params={"dataset_id": dataset_id},
    )
    assert listed.status_code == 200
    assert any(c["id"] == conversation_id for c in listed.json()["data"])

    fetched = await dataset_client.get(
        f"/api/v1/copilot/conversations/{conversation_id}",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert len(fetched.json()["data"]["messages"]) >= 2


@pytest.mark.asyncio
async def test_copilot_rejects_hallucinated_response(dataset_client: AsyncClient) -> None:
    """Validator blocks responses citing analyses that do not exist."""
    from app.application.services.copilot.response_validator import CopilotResponseValidator
    from app.shared.exceptions import BusinessValidationError

    validator = CopilotResponseValidator()
    with pytest.raises(BusinessValidationError):
        validator.enforce_or_raise(
            content="The effect is confirmed in [Statistical Analysis #5].",
            context=__import__(
                "app.application.dto.copilot", fromlist=["StructuredContext"]
            ).StructuredContext(),
        )
