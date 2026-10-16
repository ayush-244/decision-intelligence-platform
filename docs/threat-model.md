# Threat Model (STRIDE summary)

## Assets

- User credentials and JWT tokens
- Organization-scoped datasets and analytical results
- Audit logs and infrastructure configuration

## Threats & mitigations

| STRIDE | Threat | Mitigation |
|--------|--------|------------|
| Spoofing | Stolen JWT | Short-lived access tokens, httpOnly refresh, rotation |
| Tampering | Modified requests | HTTPS/HSTS, signed JWTs |
| Repudiation | Denied actions | Append-only audit log with `request_id` |
| Information disclosure | Stack traces, cross-tenant leaks | Error envelope, org-scoped queries |
| Denial of service | Flood API | Rate limits, payload caps |
| Elevation | Viewer runs admin action | RBAC on every use case |

## Trust boundaries

```
Internet → Reverse proxy (TLS) → Delphi API → PostgreSQL / Redis / Storage
```

Delphi does not trust client input — all validation server-side.

## Residual risks

- Access token in `sessionStorage` (XSS surface) — mitigate with CSP, short TTL
- Single-region deployment — address with multi-AZ in operations runbook
