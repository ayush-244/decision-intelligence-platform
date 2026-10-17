"""Version-aware analytics cache with namespace TTLs."""

from __future__ import annotations

import json
from typing import Any

from app.domain.ports.cache_store import CacheStorePort
from app.domain.value_objects.infrastructure import CACHE_TTL_SECONDS, CacheNamespace


class AnalyticsCacheService:
    """Multi-layer cache — keys always include version for invalidation safety."""

    def __init__(self, store: CacheStorePort) -> None:
        self._store = store
        self._hits = 0
        self._misses = 0

    def build_key(
        self,
        *,
        namespace: CacheNamespace,
        organization_id: str,
        dataset_id: str | None = None,
        version_id: str | None = None,
        suffix: str = "",
    ) -> str:
        parts = ["delphi", "cache", namespace.value, organization_id]
        if dataset_id:
            parts.append(dataset_id)
        if version_id:
            parts.append(f"v:{version_id}")
        if suffix:
            parts.append(suffix)
        return ":".join(parts)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        raw = await self._store.get(key)
        if raw is None:
            self._misses += 1
            return None
        self._hits += 1
        return json.loads(raw)

    async def set_json(
        self,
        *,
        key: str,
        value: dict[str, Any],
        namespace: CacheNamespace,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = ttl_seconds or CACHE_TTL_SECONDS[namespace]
        await self._store.set(key, json.dumps(value), ttl_seconds=ttl)

    async def invalidate_dataset(
        self, *, organization_id: str, dataset_id: str, version_id: str | None = None
    ) -> int:
        deleted = 0
        for namespace in CacheNamespace:
            prefix = self.build_key(
                namespace=namespace,
                organization_id=organization_id,
                dataset_id=dataset_id,
                version_id=version_id,
            )
            deleted += await self._store.delete_prefix(prefix)
        return deleted

    async def stats(self) -> dict[str, Any]:
        store_stats = await self._store.stats()
        return {
            **store_stats,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / max(self._hits + self._misses, 1),
        }

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses
