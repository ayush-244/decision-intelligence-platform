"""Async database engine and session-factory lifecycle.

The :class:`Database` object owns the SQLAlchemy ``AsyncEngine`` and a
configured ``async_sessionmaker``. Exactly one instance is created during
application startup and disposed on shutdown (see ``app.main``). Encapsulating
this in a class — rather than module-level globals — makes the lifecycle
explicit, keeps it testable, and allows multiple engines if ever needed.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings
from app.core.logging import get_logger

_logger = get_logger(__name__)


class Database:
    """Owns the async engine and session factory for the process."""

    def __init__(self, settings: Settings) -> None:
        self._engine: AsyncEngine = create_async_engine(
            settings.database_url_str,
            echo=False,
            pool_pre_ping=True,  # transparently recycle stale connections
            pool_size=10,
            max_overflow=5,
            pool_recycle=1800,  # guard against server-side idle timeouts (30 min)
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
        )
        _logger.info("database_engine_initialised")

    @property
    def engine(self) -> AsyncEngine:
        """The underlying async engine (used by Alembic and health probes)."""
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Factory producing request-scoped async sessions."""
        return self._session_factory

    async def dispose(self) -> None:
        """Dispose the connection pool on application shutdown."""
        await self._engine.dispose()
        _logger.info("database_engine_disposed")
