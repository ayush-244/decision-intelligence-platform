"""Redis connection lifecycle.

Wraps a single ``redis.asyncio`` connection pool created at startup and closed
at shutdown. Named ``RedisClient`` (not ``RedisCache``) because caching is not
implemented yet — the name reflects what it actually does today.
"""

from __future__ import annotations

from redis.asyncio import Redis, from_url

from app.core.config import Settings
from app.core.logging import get_logger

_logger = get_logger(__name__)


class RedisClient:
    """Owns the async Redis client / connection pool for the process."""

    def __init__(self, settings: Settings) -> None:
        self._client: Redis = from_url(
            settings.redis_url_str,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
        )
        _logger.info("redis_client_initialised")

    @property
    def client(self) -> Redis:
        """The underlying async Redis client."""
        return self._client

    async def close(self) -> None:
        """Close the client and its connection pool on shutdown."""
        await self._client.aclose()
        _logger.info("redis_client_closed")
