"""Unit tests for the CheckSystemHealthUseCase."""

from __future__ import annotations

import pytest

from app.application.use_cases import CheckSystemHealthUseCase
from app.domain.entities.health import HealthStatus
from tests.fakes import FakeHealthProbe

pytestmark = pytest.mark.unit


async def test_empty_probe_set_is_healthy() -> None:
    result = await CheckSystemHealthUseCase([]).execute()
    assert result.status is HealthStatus.HEALTHY


async def test_aggregates_all_probes() -> None:
    probes = [
        FakeHealthProbe("postgres", HealthStatus.HEALTHY),
        FakeHealthProbe("redis", HealthStatus.HEALTHY),
    ]
    result = await CheckSystemHealthUseCase(probes).execute()
    assert result.status is HealthStatus.HEALTHY
    assert {c.name for c in result.components} == {"postgres", "redis"}


async def test_probe_timeout_is_reported_unhealthy() -> None:
    probes = [FakeHealthProbe("slow", delay_seconds=0.2)]
    result = await CheckSystemHealthUseCase(probes, timeout_seconds=0.01).execute()
    assert result.status is HealthStatus.UNHEALTHY
    assert result.components[0].detail is not None
    assert "Timed out" in result.components[0].detail


async def test_probe_exception_is_reported_unhealthy() -> None:
    probes = [FakeHealthProbe("boom", raises=RuntimeError("kaboom"))]
    result = await CheckSystemHealthUseCase(probes).execute()
    assert result.status is HealthStatus.UNHEALTHY
    assert not result.is_ready
