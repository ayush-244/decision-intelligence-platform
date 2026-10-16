"""Integration tests for centralized exception handling."""

from __future__ import annotations

from http import HTTPStatus

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_not_found_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/__test__/not-found")
    assert response.status_code == HTTPStatus.NOT_FOUND
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Resource missing"
    assert response.headers.get("X-Request-ID") == body["error"]["request_id"]


async def test_business_validation_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/__test__/business-validation")
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response.json()["error"]["code"] == "validation_error"


async def test_unexpected_error_is_opaque(client: AsyncClient) -> None:
    response = await client.get("/__test__/unexpected")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"] == "An unexpected error occurred."
    assert "unexpected failure" not in body["error"]["message"]


async def test_delphi_error_preserves_custom_code(client: AsyncClient) -> None:
    response = await client.get("/__test__/delphi-generic")
    assert response.status_code == 418
    assert response.json()["error"]["code"] == "custom_error"
