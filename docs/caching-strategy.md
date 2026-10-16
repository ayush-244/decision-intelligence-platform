# Caching Strategy

Delphi uses **version-aware, namespaced Redis keys** so analytical results are never served stale after dataset or version changes.

## Key format

```
delphi:cache:{namespace}:{organization_id}:{dataset_id}:v:{version_id}:{suffix}
```

`version_id` is required for analysis, simulation, recommendation, and dashboard namespaces. Metadata and schema caches include dataset scope; invalidation walks all namespaces for a dataset.

## Namespaces and TTLs

| Namespace | TTL | Rationale |
|-----------|-----|-----------|
| `dataset_metadata` | 1h | Changes infrequently; invalidated on upload |
| `schema` | 2h | Stable per version |
| `analysis` | 30m | Statistical/causal outputs |
| `simulation` | 30m | Scenario results |
| `recommendation` | 15m | Decision outputs change more often |
| `dashboard` | 5m | Executive aggregates |
| `search` | 2m | Workspace search is highly dynamic |

## Invalidation

1. **Dataset-scoped:** `POST /api/v1/infrastructure/cache/invalidate` deletes all namespace prefixes for `organization + dataset (+ version)`.
2. **Version bump:** new `version_id` in cache keys naturally misses old entries.
3. **TTL expiry:** safety net; never relied on for correctness.

## Redis usage summary

| Use | Key pattern |
|-----|-------------|
| Analytics cache | `delphi:cache:*` |
| Job queue | `delphi:jobs:queue` |
| Cancelled jobs | `delphi:jobs:removed` (set) |
| Rate limits (foundation) | `delphi:ratelimit:*` (reserved) |
| Session cache (foundation) | `delphi:session:*` (reserved) |

Tests use `InMemoryCacheStore` when Redis is not available.
