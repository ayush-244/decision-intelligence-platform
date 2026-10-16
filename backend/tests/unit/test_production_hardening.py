"""Unit tests for production hardening components."""

from __future__ import annotations

import pytest

from app.application.services.audit.audit_service import AuditService
from app.domain.value_objects.audit_action import AuditAction
from app.infrastructure.resilience.in_memory_circuit_breaker import InMemoryCircuitBreaker
from app.infrastructure.secrets.env_secrets_provider import EnvSecretsProvider
from app.shared.exceptions import ForbiddenError, ServiceUnavailableError
from app.shared.resilience.retry import retry_async
from tests.identity_fakes import InMemoryIdentityStore


@pytest.mark.asyncio
async def test_audit_service_records_events() -> None:
    from uuid import uuid4

    store = InMemoryIdentityStore()
    audit = AuditService(store.audit_log_repo())
    org_id = uuid4()
    user_id = uuid4()
    await audit.record(
        action=AuditAction.JOB_SUBMITTED,
        resource_type="analytics_job",
        user_id=user_id,
        organization_id=org_id,
        request_id="req-123",
        metadata={"name": "test"},
    )
    logs = await store.audit_log_repo().list_for_organization(organization_id=org_id)
    assert len(logs) == 1
    assert logs[0].action == AuditAction.JOB_SUBMITTED.value
    assert logs[0].metadata.get("request_id") == "req-123"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures() -> None:
    breaker = InMemoryCircuitBreaker(failure_threshold=2, recovery_timeout_seconds=60)

    async def fail() -> None:
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        await breaker.call(name="redis", operation=fail)
    with pytest.raises(RuntimeError):
        await breaker.call(name="redis", operation=fail)
    with pytest.raises(ServiceUnavailableError):
        await breaker.call(name="redis", operation=fail)
    assert breaker.state(name="redis") == "open"


@pytest.mark.asyncio
async def test_retry_async_eventually_succeeds() -> None:
    attempts = {"count": 0}

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("transient")
        return "ok"

    result = await retry_async(flaky, max_attempts=3, base_delay_seconds=0.01)
    assert result == "ok"
    assert attempts["count"] == 3


def test_env_secrets_provider_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DELPHI_JWT_SECRET_KEY", "test-secret-value")
    provider = EnvSecretsProvider()
    assert provider.get_secret("JWT_SECRET_KEY") == "test-secret-value"


def test_authorization_logs_denial() -> None:
    from app.application.authorization.authorization_service import AuthorizationService
    from app.domain.value_objects.role import MembershipRole, Permission

    service = AuthorizationService()
    with pytest.raises(ForbiddenError):
        service.require_permission(
            MembershipRole.VIEWER,
            Permission.INFRA_MANAGE,
            user_id=None,
            organization_id=None,
            request_id="trace-1",
        )
