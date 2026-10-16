# Observability Guide

## Structured logging

All logs use **structlog** with JSON (production) or console (development) rendering.

Per-request context:

- `request_id` — from `X-Request-ID`
- `trace_id` — from `X-Trace-ID` or W3C `traceparent`
- `method`, `path` — access log fields

## Security events

Logged at `WARNING`:

- `authorization_denied` — RBAC failure with permission, role, user
- `rate_limit_exceeded` — throttled client

Logged at `INFO`:

- `audit_event` — immutable audit trail mirror

## Metrics (in-process)

`MetricsCollector` tracks:

- Cache hit/miss rates
- Slow query detection (`DELPHI_SLOW_QUERY_THRESHOLD_MS`)
- Job durations

## OpenTelemetry readiness

Trace context middleware parses W3C `traceparent`. Future OTel SDK export attaches to the same `trace_id` without router changes.

## Support workflow

When users report errors, collect:

1. `request_id` from error response
2. Timestamp (UTC)
3. Organization ID
4. User action performed

Search logs: `request_id="<uuid>"`
