"""Shared pytest fixtures.

Provides an app instance built from deterministic test settings and an async
HTTP client bound to it via ASGI transport. Dependency providers are overridden
so tests never touch a real database or Redis.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Environment, LogFormat, Settings, get_settings
from app.main import create_app
from app.presentation.api import deps
from app.shared.exceptions import BusinessValidationError, DelphiError, NotFoundError
from tests.fakes import FakeHealthProbe
from tests.identity_fakes import InMemoryIdentityStore
from tests.dataset_fakes import InMemoryDatasetStore
from tests.infrastructure_fakes import InMemoryInfrastructureStore
from tests.copilot_fakes import InMemoryCopilotStore


@pytest.fixture(autouse=True)
def _bind_test_settings(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure auth rate limits and other settings reads use the test fixture."""
    get_settings.cache_clear()
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.presentation.api.v1.routers.auth.get_settings", lambda: settings)


@pytest.fixture
def settings() -> Settings:
    """Deterministic settings for tests (no external services required)."""
    return Settings(
        environment=Environment.DEVELOPMENT,
        debug=False,
        log_format=LogFormat.CONSOLE,
        cors_origins=[],
        auth_rate_limit="1000/minute",
        api_rate_limit="10000/minute",
        max_request_body_bytes=10_485_760,
    )


@pytest.fixture
def app(settings: Settings) -> Iterator[FastAPI]:
    """A FastAPI app configured for testing.

    The lifespan is intentionally not run: infrastructure clients are lazy and
    the DI providers exercised by tests are overridden per-test, so no real
    connections are opened.
    """
    application = create_app(settings)
    _register_test_routes(application)
    yield application


def _register_test_routes(app: FastAPI) -> None:
    """Routes used only by tests to exercise error handling tiers."""
    router = APIRouter(prefix="/__test__", tags=["test"])

    @router.get("/not-found")
    async def trigger_not_found() -> None:
        raise NotFoundError("Resource missing")

    @router.get("/business-validation")
    async def trigger_business_validation() -> None:
        raise BusinessValidationError("Invalid business rule")

    @router.get("/unexpected")
    async def trigger_unexpected() -> None:
        raise RuntimeError("unexpected failure")

    @router.get("/delphi-generic")
    async def trigger_delphi_generic() -> None:
        raise DelphiError("Something went wrong", code="custom_error", status_code=418)

    app.include_router(router)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async HTTP client bound to the ASGI app."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest.fixture
def identity_store() -> InMemoryIdentityStore:
    return InMemoryIdentityStore()


@pytest.fixture
def identity_app(app: FastAPI, identity_store: InMemoryIdentityStore) -> FastAPI:
    """App with in-memory identity repositories (no database required)."""
    store = identity_store
    app.dependency_overrides[deps.get_user_repository] = lambda: store.user_repo()
    app.dependency_overrides[deps.get_organization_repository] = lambda: store.organization_repo()
    app.dependency_overrides[deps.get_membership_repository] = lambda: store.membership_repo()
    app.dependency_overrides[deps.get_workspace_repository] = lambda: store.workspace_repo()
    app.dependency_overrides[deps.get_project_repository] = lambda: store.project_repo()
    app.dependency_overrides[deps.get_refresh_token_repository] = lambda: store.refresh_token_repo()
    app.dependency_overrides[deps.get_audit_log_repository] = lambda: store.audit_log_repo()
    return app


@pytest.fixture
async def identity_client(identity_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=identity_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest.fixture
def dataset_store() -> InMemoryDatasetStore:
    return InMemoryDatasetStore()


@pytest.fixture
def infrastructure_store() -> InMemoryInfrastructureStore:
    return InMemoryInfrastructureStore()


@pytest.fixture
def copilot_store() -> InMemoryCopilotStore:
    return InMemoryCopilotStore()


@pytest.fixture
def dataset_app(
    identity_app: FastAPI,
    dataset_store: InMemoryDatasetStore,
    infrastructure_store: InMemoryInfrastructureStore,
    copilot_store: InMemoryCopilotStore,
    settings: Settings,
    tmp_path,
) -> FastAPI:
    """App with in-memory identity and dataset repositories (no database required)."""
    test_settings = settings.model_copy(update={"storage_base_path": tmp_path / "storage"})
    identity_app.dependency_overrides[deps.get_settings] = lambda: test_settings
    identity_app.dependency_overrides[deps.get_dataset_repository] = (
        lambda: dataset_store.dataset_repo()
    )
    identity_app.dependency_overrides[deps.get_dataset_version_repository] = (
        lambda: dataset_store.version_repo()
    )
    identity_app.dependency_overrides[deps.get_dataset_file_repository] = (
        lambda: dataset_store.file_repo()
    )
    identity_app.dependency_overrides[deps.get_upload_job_repository] = (
        lambda: dataset_store.job_repo()
    )
    identity_app.dependency_overrides[deps.get_schema_snapshot_repository] = (
        lambda: dataset_store.schema_repo()
    )
    identity_app.dependency_overrides[deps.get_validation_report_repository] = (
        lambda: dataset_store.validation_repo()
    )
    identity_app.dependency_overrides[deps.get_dataset_statistics_repository] = (
        lambda: dataset_store.statistics_repo()
    )
    identity_app.dependency_overrides[deps.get_intelligence_report_repository] = (
        lambda: dataset_store.intelligence_repo()
    )
    identity_app.dependency_overrides[deps.get_statistical_analysis_repository] = (
        lambda: dataset_store.statistical_analysis_repo()
    )
    identity_app.dependency_overrides[deps.get_causal_analysis_repository] = (
        lambda: dataset_store.causal_analysis_repo()
    )
    identity_app.dependency_overrides[deps.get_dag_version_repository] = (
        lambda: dataset_store.dag_version_repo()
    )
    identity_app.dependency_overrides[deps.get_simulation_run_repository] = (
        lambda: dataset_store.simulation_run_repo()
    )
    identity_app.dependency_overrides[deps.get_simulation_scenario_repository] = (
        lambda: dataset_store.simulation_scenario_repo()
    )
    identity_app.dependency_overrides[deps.get_decision_run_repository] = (
        lambda: dataset_store.decision_run_repo()
    )
    identity_app.dependency_overrides[deps.get_executive_report_repository] = (
        lambda: dataset_store.executive_report_repo()
    )
    identity_app.dependency_overrides[deps.get_decision_session_repository] = (
        lambda: dataset_store.decision_session_repo()
    )
    identity_app.dependency_overrides[deps.get_session_activity_repository] = (
        lambda: dataset_store.session_activity_repo()
    )
    infra = infrastructure_store
    identity_app.dependency_overrides[deps.get_analytics_job_repository] = lambda: infra.job_repo()
    identity_app.dependency_overrides[deps.get_copilot_conversation_repository] = (
        lambda: copilot_store.conversation_repo()
    )
    identity_app.dependency_overrides[deps.get_copilot_message_repository] = (
        lambda: copilot_store.message_repo()
    )
    identity_app.state.job_queue = infra.queue
    identity_app.state.cache_store = infra.cache
    return identity_app


@pytest.fixture
async def dataset_client(dataset_app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=dataset_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest.fixture
def fake_probe_factory() -> type[FakeHealthProbe]:
    """Expose the fake probe class for tests that build custom probe sets."""
    return FakeHealthProbe
