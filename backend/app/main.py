"""Application entrypoint and composition root.

Builds the FastAPI application via a factory (``create_app``) so tests can
construct isolated instances. Infrastructure with a lifecycle (database engine,
Redis client) is created on startup and disposed on shutdown using the ASGI
lifespan protocol, and stored on ``app.state`` for the DI providers to read.

Run with: ``uvicorn app.main:create_app --factory``
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.presentation.rate_limit import limiter

from app import __version__
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.application.services.infrastructure.worker import BackgroundWorker, RepoOperation
from app.infrastructure.cache import RedisClient
from app.infrastructure.database import Database
from app.infrastructure.database.session import session_scope
from app.presentation.api.routers import system_router
from app.presentation.api.v1 import api_v1_router
from app.presentation.errors import register_exception_handlers
from app.presentation.middleware import (
    ContentTypeValidationMiddleware,
    PayloadSizeLimitMiddleware,
    RequestContextMiddleware,
    TraceContextMiddleware,
)
from app.presentation.middleware.security_headers import SecurityHeadersMiddleware

_logger = get_logger(__name__)

# Explicit CORS allowlists — never use wildcard methods/headers with credentials.
_CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_CORS_HEADERS = [
    "Authorization",
    "Content-Type",
    "X-Organization-ID",
    "X-Request-ID",
    "X-Trace-ID",
    "Idempotency-Key",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup/shutdown of stateful infrastructure."""
    settings: Settings = app.state.settings
    _logger.info("application_startup", environment=settings.environment.value)

    database = Database(settings)
    redis = RedisClient(settings)
    app.state.database = database
    app.state.redis = redis

    worker: BackgroundWorker | None = None
    if settings.worker_enabled:
        from app.infrastructure.cache.redis_cache_store import RedisCacheStore
        from app.infrastructure.database.repositories.analytics_job_repository import (
            SqlAlchemyAnalyticsJobRepository,
        )
        from app.infrastructure.queue.redis_job_queue import RedisJobQueue

        app.state.job_queue = RedisJobQueue(redis.client)
        app.state.cache_store = RedisCacheStore(redis.client)

        async def run_with_repo(operation: RepoOperation[Any]) -> Any:
            async with session_scope(database.session_factory) as session:
                repo = SqlAlchemyAnalyticsJobRepository(session)
                return await operation(repo)

        worker = BackgroundWorker(run_with_repo, app.state.job_queue)
        await worker.start(poll_interval=settings.worker_poll_interval_seconds)
        app.state.background_worker = worker

    try:
        yield
    finally:
        if worker is not None:
            await worker.stop()
        await redis.close()
        await database.dispose()
        _logger.info("application_shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a FastAPI application instance."""
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="AI-Powered Decision Intelligence Platform",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.limiter = limiter
    limiter._default_limits = [settings.api_rate_limit]  # noqa: SLF001

    _configure_middleware(app, settings)
    register_exception_handlers(app)
    _register_routers(app, settings)

    return app


def _configure_middleware(app: FastAPI, settings: Settings) -> None:
    """Attach middleware. Order matters: outermost is added last."""
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=_CORS_METHODS,
            allow_headers=_CORS_HEADERS,
        )
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(ContentTypeValidationMiddleware)
    app.add_middleware(PayloadSizeLimitMiddleware, max_bytes=settings.max_request_body_bytes)
    app.add_middleware(SecurityHeadersMiddleware, environment=settings.environment)
    app.add_middleware(TraceContextMiddleware)
    app.add_middleware(RequestContextMiddleware)


def _register_routers(app: FastAPI, settings: Settings) -> None:
    """Mount operational (root) and versioned routers."""
    app.include_router(system_router)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
