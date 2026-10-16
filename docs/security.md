# Production Security Guide (Phase 12)

Delphi assumes every request is untrusted. Phase 12 hardens APIs, authorization, audit, and observability for enterprise deployment.

## Defense layers

| Layer | Mechanism |
|-------|-----------|
| Transport | HSTS + CSP in staging/production |
| Request | Payload size limits, Content-Type validation, global rate limits |
| AuthN | JWT access tokens + httpOnly refresh cookies |
| AuthZ | Central RBAC via `AuthorizationService` |
| Data | Parameterized SQLAlchemy, path traversal checks in storage |
| Audit | Append-only `audit_logs` with `request_id` metadata |
| Errors | Standard `ErrorResponse` envelope — no stack traces |

## Rate limiting

- **Global:** `DELPHI_API_RATE_LIMIT` (default `200/minute`) via SlowAPI
- **Auth:** `DELPHI_AUTH_RATE_LIMIT` (stricter, per-route)
- **429 responses** use the standard error envelope (`rate_limit_exceeded`)

## Headers

Production/staging responses include:

- `Strict-Transport-Security`
- `Content-Security-Policy`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Cross-Origin-Opener-Policy: same-origin`

## Correlation & tracing

- `X-Request-ID` — per-request correlation (required for support)
- `X-Trace-ID` / W3C `traceparent` — distributed tracing foundation
- Both echoed on responses and bound to structured logs

## Secrets

`EnvSecretsProvider` reads `DELPHI_*` environment variables today. The `SecretsProvider` port supports future HashiCorp Vault / cloud secret managers without changing call sites.

**Rotation:** deploy new `DELPHI_JWT_SECRET_KEY`, accept both keys during overlap, revoke old refresh tokens.

## Idempotency

Clients may send `Idempotency-Key` on mutating requests (foundation in Phase 12). Keys are scoped per organization in Redis.

## Threat mitigations

| Threat | Mitigation |
|--------|------------|
| SQL injection | SQLAlchemy ORM, no raw string SQL |
| XSS | CSP, JSON APIs, React escaping |
| CSRF | SameSite=Lax refresh cookie, Bearer access token |
| Path traversal | Storage key normalization |
| Mass assignment | Pydantic schemas, explicit DTOs |
| Upload abuse | `max_upload_size_bytes`, file validator |

See [Threat Model](threat-model.md) and [ADR 012](adr/012-production-hardening.md).
