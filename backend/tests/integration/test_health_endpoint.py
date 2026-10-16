"""Integration tests for the readiness endpoint using fake probes.

The ``CheckSystemHealthUseCase`` dependency is overridden so we exercise the
full HTTP path (routing, schema mapping, status-code logic) without a real
database or Redis.
"""

from __future__ import annotations

from http import HTTPStatus

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.application.use_cases import CheckSystemHealthUseCase
from app.domain.entities.health import HealthStatus
from app.presentation.api.deps import get_check_system_health_use_case
from tests.fakes import FakeHealthProbe

pytestmark = pytest.mark.integration


def _override_with(app: FastAPI, *probes: FakeHealthProbe) -> None:
    app.dependency_overrides[get_check_system_health_use_case] = lambda: CheckSystemHealthUseCase(
        list(probes)
    )


async def test_readiness_healthy_returns_200(app: FastAPI, client: AsyncClient) -> None:
    _override_with(
        app,
        FakeHealthProbe("postgres", HealthStatus.HEALTHY),
        FakeHealthProbe("redis", HealthStatus.HEALTHY),
    )
    response = await client.get("/api/v1/health")
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["status"] == "healthy"
    assert len(body["components"]) == 2


async def test_readiness_unhealthy_returns_503(app: FastAPI, client: AsyncClient) -> None:
    _override_with(
        app,
        FakeHealthProbe("postgres", HealthStatus.UNHEALTHY, detail="down"),
        FakeHealthProbe("redis", HealthStatus.HEALTHY),
    )
    response = await client.get("/api/v1/health")
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json()["status"] == "unhealthy"
