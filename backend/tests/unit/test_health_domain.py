"""Unit tests for the system-health domain model."""

from __future__ import annotations

import pytest

from app.domain.entities.health import ComponentHealth, HealthStatus, SystemHealth

pytestmark = pytest.mark.unit


def test_no_components_is_healthy() -> None:
    system = SystemHealth.from_components(())
    assert system.status is HealthStatus.HEALTHY
    assert system.is_ready


def test_all_healthy_components_aggregate_to_healthy() -> None:
    components = (
        ComponentHealth("postgres", HealthStatus.HEALTHY),
        ComponentHealth("redis", HealthStatus.HEALTHY),
    )
    system = SystemHealth.from_components(components)
    assert system.status is HealthStatus.HEALTHY
    assert system.is_ready


def test_overall_status_is_worst_component() -> None:
    components = (
        ComponentHealth("postgres", HealthStatus.HEALTHY),
        ComponentHealth("redis", HealthStatus.DEGRADED),
    )
    system = SystemHealth.from_components(components)
    assert system.status is HealthStatus.DEGRADED
    assert system.is_ready  # degraded still accepts traffic


def test_unhealthy_component_makes_system_not_ready() -> None:
    components = (
        ComponentHealth("postgres", HealthStatus.UNHEALTHY),
        ComponentHealth("redis", HealthStatus.HEALTHY),
    )
    system = SystemHealth.from_components(components)
    assert system.status is HealthStatus.UNHEALTHY
    assert not system.is_ready


def test_severity_ordering() -> None:
    assert HealthStatus.HEALTHY.severity < HealthStatus.DEGRADED.severity
    assert HealthStatus.DEGRADED.severity < HealthStatus.UNHEALTHY.severity
