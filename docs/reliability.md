# Reliability Guide

## Resilience patterns

### Health probes

| Probe | Endpoint | Critical |
|-------|----------|----------|
| Liveness | `GET /health` | Process up |
| Readiness | `GET /api/v1/health` | DB, Redis, storage |

Readiness returns **503** when any critical dependency is unhealthy.

### Circuit breaker

`InMemoryCircuitBreaker` wraps dependency calls. After `DELPHI_CIRCUIT_BREAKER_FAILURE_THRESHOLD` failures (default 5), the circuit opens for `DELPHI_CIRCUIT_BREAKER_RECOVERY_SECONDS` (default 30s).

### Retry

`retry_async()` provides exponential backoff for transient failures (DB blips, network timeouts).

### Dead-letter queue

Failed background jobs can be pushed to `DeadLetterQueuePort` for manual replay (foundation — in-memory in tests, Redis list in production path).

## Failure recovery

| Failure | Behavior |
|---------|----------|
| Database down | Readiness 503, user-friendly `service_unavailable` |
| Redis down | Readiness degraded; in-memory fallbacks in dev/tests |
| Storage down | Readiness 503 via `StorageHealthProbe` |
| Worker down | Jobs remain queued; API still accepts submissions |
| Rate limit | 429 with retry guidance |

No silent failures — all errors use the standard envelope with `request_id`.

## Graceful degradation

- Health checks timeout per-probe (`HEALTH_PROBE_TIMEOUT_SECONDS`)
- Worker optional (`DELPHI_WORKER_ENABLED=false`) — API remains functional
- Cache miss falls through to origin computation
