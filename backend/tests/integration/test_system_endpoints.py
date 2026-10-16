"""Integration tests for root/liveness/version endpoints.

These do not require the lifespan or any datastore.
"""

from __future__ import annotations

from http import HTTPStatus

import pytest
from httpx import AsyncClient

from app import __version__

pytestmark = pytest.mark.integration


async def test_root_returns_service_metadata(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["name"] == "Delphi"
    assert body["version"] == __version__
    assert body["tagline"]


async def test_liveness_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


async def test_version_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/version")
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["version"] == __version__
    assert body["environment"] == "development"


async def test_request_id_header_present(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.headers.get("X-Request-ID")


async def test_inbound_request_id_is_echoed(client: AsyncClient) -> None:
    correlation_id = "test-correlation-123"
    response = await client.get("/health", headers={"X-Request-ID": correlation_id})
    assert response.headers.get("X-Request-ID") == correlation_id


async def test_invalid_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/health", headers={"X-Request-ID": "bad id with spaces!"})
    echoed = response.headers.get("X-Request-ID")
    assert echoed is not None
    assert echoed != "bad id with spaces!"
