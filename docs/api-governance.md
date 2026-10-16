# API Governance

## Versioning

- Current surface: `/api/v1`
- Breaking changes require `/api/v2` — no silent breaking changes in-place
- Deprecation notice: minimum **90 days** before sunset (`GET /api/v1/governance/versioning`)

## Error contract

All errors return:

```json
{
  "error": {
    "code": "forbidden",
    "message": "Human-readable message",
    "details": {},
    "request_id": "uuid"
  }
}
```

Catalog: `GET /api/v1/governance/errors`

## Pagination

Use `limit` (1–200, default 50) and `offset` (≥ 0). List responses use `{ "data": [...], "meta": { "total": N } }` where applicable.

## Sorting & filtering

- `sort_by` — field name (max 64 chars)
- `sort_order` — `asc` | `desc`
- Filters via query parameters documented per resource

## Idempotency

Send `Idempotency-Key` header on `POST` mutations that create resources. Duplicate in-flight keys return `409 idempotency_conflict`.

## Correlation headers

| Header | Purpose |
|--------|---------|
| `X-Request-ID` | Support correlation |
| `X-Trace-ID` | Trace propagation |
| `Idempotency-Key` | Safe retries |
