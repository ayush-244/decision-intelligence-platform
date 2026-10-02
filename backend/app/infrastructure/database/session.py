"""Request-scoped session provisioning.

``session_scope`` yields an :class:`AsyncSession` and guarantees commit on
success / rollback on error / close always. The FastAPI dependency in
``app.presentation.api.deps`` adapts this into an injectable ``AsyncSession``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Provide a transactional scope around a series of operations."""
    session = session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
