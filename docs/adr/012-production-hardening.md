# ADR 012: Production Hardening

## Status

Accepted — Phase 12

## Context

Phases 1–11 delivered full analytical capabilities and enterprise infrastructure. Before customer deployment, Delphi requires security, reliability, observability, and operational maturity — without new business features.

## Decision

1. **Middleware stack:** Request context → trace context → security headers → payload limits → content-type validation → SlowAPI rate limiting.
2. **Unified error envelope** for all failures including rate limits (no slowapi default HTML/JSON mismatch).
3. **Central `AuditService`** with canonical `AuditAction` enum and `request_id` in metadata.
4. **`SecretsProvider` port** with `EnvSecretsProvider` default; Vault-ready.
5. **Circuit breaker + retry** utilities for dependency resilience.
6. **DLQ port** for failed job recovery foundation.
7. **Governance APIs** (`/governance/errors`, `/governance/versioning`).
8. **Storage health probe** added to readiness.
9. **Frontend:** session expiry UX, 403 toasts, error states, offline hook foundation.

## Consequences

- All API errors are machine-parseable with correlation IDs.
- Production deployments must terminate TLS at proxy; HSTS assumes HTTPS.
- Audit coverage expands incrementally — infrastructure mutations audited in Phase 12.
- OpenTelemetry export is a future attach point, not a new dependency today.

## Alternatives considered

- **RFC 7807 Problem Details:** rejected to avoid dual error formats; existing envelope is sufficient.
- **API gateway rate limiting only:** rejected; in-app limits protect direct exposure and dev environments.
