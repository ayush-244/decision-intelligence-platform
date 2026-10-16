# ADR 011: Enterprise Analytics Infrastructure

## Status

Accepted — Phase 11

## Context

Phases 1–10 implemented synchronous API handlers for intelligence, statistics, causal, simulation, decision, and executive workloads. Enterprise deployments require:

- Background execution for long-running analyses
- Redis-backed queue and cache
- Job monitoring and observability foundations
- Infrastructure APIs and dashboard

## Decision

1. **Persist jobs in PostgreSQL**, enqueue in **Redis lists** (`BLPOP`/`RPUSH`).
2. **Version-aware cache keys** across seven namespaces with explicit invalidation API.
3. **Modular monolith services:** `JobOrchestrator`, `QueueManager`, `BackgroundWorker`, `AnalyticsCacheService`, `ExecutionMonitor`, `MetricsCollector`, `PerformanceProfiler`.
4. **Worker optional** via `DELPHI_WORKER_ENABLED`; API remains functional without worker (jobs stay queued).
5. **In-memory adapters** for tests when lifespan/Redis is not started.
6. **No new business logic** — worker default handler simulates progress; future phases wire real engines as job handlers.

## Consequences

- Users submit jobs via `POST /api/v1/jobs` and poll status instead of blocking HTTP requests.
- Redis becomes required for production queue/cache; PostgreSQL remains source of truth for job history.
- OpenTelemetry export can attach to `MetricsCollector` and structured logs without router changes.

## Alternatives considered

- **Celery/RQ:** rejected to keep dependency surface small; Redis list queue is sufficient for modular monolith.
- **Cache-aside only in engines:** rejected; centralized `AnalyticsCacheService` enforces key/version conventions.
