# Enterprise Analytics Infrastructure (Phase 11)

Phase 11 prepares Delphi for enterprise-scale analytical workloads without adding new business features. Long-running work moves off the request thread into a background job system backed by Redis, with version-aware caching, observability foundations, and an infrastructure dashboard.

## Architecture

```
Job Orchestrator → Queue Manager → Background Workers
        ↓                ↓
Analytics Cache ← Metadata Cache (namespaced keys)
        ↓
Storage Manager (existing StorageProvider port)
        ↓
Execution Monitor / Metrics Collector / Performance Profiler
        ↓
Infrastructure APIs + Dashboard
```

Each module has a single responsibility and is wired through FastAPI dependency injection.

## Background jobs

Jobs are persisted in PostgreSQL (`analytics_jobs`) and enqueued in Redis (`delphi:jobs:queue`).

**Lifecycle:** `queued` → `running` → `completed` | `failed` | `cancelled`, with `retrying` on manual retry.

**Job types:** dataset processing, data intelligence, statistics, causal analysis, simulation, decision, executive report.

Enable the worker process:

```bash
DELPHI_WORKER_ENABLED=true uvicorn app.main:create_app --factory
```

## APIs

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/jobs` | Submit job (202 Accepted) |
| `GET /api/v1/jobs` | List organization jobs |
| `GET /api/v1/jobs/{id}` | Job status, progress, logs |
| `POST /api/v1/jobs/{id}/cancel` | Cancel job |
| `POST /api/v1/jobs/{id}/retry` | Retry failed job |
| `GET /api/v1/infrastructure/metrics` | Queue, job, cache metrics |
| `GET /api/v1/infrastructure/cache/stats` | Cache hit/miss stats |
| `POST /api/v1/infrastructure/cache/invalidate` | Invalidate dataset cache |
| `GET /api/v1/infrastructure/queue` | Queue depth |

## Permissions

- `job:read`, `job:create`, `job:cancel` — analysts and above
- `infra:read` — viewers can monitor
- `infra:manage` — admins/owners (cache invalidation)

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `DELPHI_WORKER_ENABLED` | `false` | Start background worker in lifespan |
| `DELPHI_WORKER_POLL_INTERVAL_SECONDS` | `1.0` | Queue poll interval |
| `DELPHI_JOB_MAX_RETRIES` | `3` | Max automatic retry attempts |
| `DELPHI_SLOW_QUERY_THRESHOLD_MS` | `500` | Slow query metric threshold |
| `DELPHI_CACHE_ENABLED` | `true` | Enable Redis analytics cache |

See also [Caching Strategy](caching-strategy.md) and [ADR 011](adr/011-enterprise-infrastructure.md).
