# Operational Runbook

## Startup

```bash
cd backend && uv run alembic upgrade head
DELPHI_WORKER_ENABLED=true uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

Verify: `GET /health` → 200, `GET /api/v1/health` → 200 healthy.

## Health checks

| Check | Expected |
|-------|----------|
| Liveness | 200, no I/O |
| Readiness | 200 when DB+Redis+storage healthy |
| Metrics | `GET /api/v1/infrastructure/metrics` (authenticated) |

## Common issues

**Readiness 503 — database:** verify `DELPHI_DATABASE_URL`, connection pool, migrations applied.

**Readiness 503 — redis:** verify `DELPHI_REDIS_URL`, network ACLs.

**Jobs stuck queued:** confirm `DELPHI_WORKER_ENABLED=true` and worker process running.

**High 429 rate:** adjust `DELPHI_API_RATE_LIMIT` or scale horizontally behind load balancer.

## Logs

```bash
# JSON logs — filter by request_id
jq 'select(.request_id=="<uuid>")' < app.log
```

## Backups

- PostgreSQL: daily logical backup (pg_dump) minimum
- Storage: replicate `DELPHI_STORAGE_BASE_PATH` or object storage bucket

See [Incident Response](incident-response.md).
