# Architecture

This document explains how Delphi is structured and, more importantly, **why**. It is the
reference every contributor should read before adding a module.

## Guiding principles

1. **Statistical rigor over LLM magic.** The analytical core is deterministic, testable, and
   explainable. LLMs are confined to a future explanation layer that narrates results.
2. **Clean Architecture with an inward-only dependency rule.** Business logic never depends on
   frameworks or I/O.
3. **Modular monolith, not microservices (yet).** One deployable unit keeps operations simple.
   Clean boundaries mean a module can be extracted into a service later without a rewrite.
4. **Maintainability over cleverness.** Written as if 20 engineers will maintain it for five years.

## Why a modular monolith

Microservices introduce network partitions, distributed transactions, versioned contracts, and
heavy operational tooling. None of that buys us anything while the product is a single analytics
engine with shared data. A modular monolith gives us:

- Atomic refactors across the API contract and its consumers.
- Simple local development (`docker compose up`).
- One CI pipeline and one deploy.

The layered boundaries below are the insurance policy: if one module (say, the simulation engine)
ever needs independent scaling, its ports/adapters seam already exists.

## The layers

Dependencies point **inward only**. An arrow means "may import".

```
Presentation ──▶ Application ──▶ Domain ◀── Infrastructure
      │                │            ▲             │
      └────────────────┴────────────┴─────────────┘
                    Core / Shared (cross-cutting)
```

### Domain (`app/domain`)
Pure Python. Entities, value objects, and **repository interfaces (ports)**. No FastAPI, no
SQLAlchemy, no Redis. This is the most stable, most tested layer. Example: `HealthProbe` (a port)
and the `SystemHealth` value object.

### Application (`app/application`)
Orchestrates domain logic into **use-cases** (interactors). Depends on the domain and on
abstractions only. Example: `CheckSystemHealthUseCase` runs a set of `HealthProbe`s concurrently
with per-probe timeouts and aggregates the result. DTOs here are plain dataclasses — deliberately
framework-free.

### Infrastructure (`app/infrastructure`)
The only layer allowed to import third-party I/O libraries. Implements domain ports and manages
technical lifecycles: the async SQLAlchemy engine/session, the Redis client, and the concrete
`DatabaseHealthProbe` / `RedisHealthProbe`.

### Presentation (`app/presentation`)
The HTTP delivery mechanism (FastAPI). Routers, middleware, Pydantic request/response schemas,
centralised exception handlers, and the **composition root** (`api/deps.py`) that wires ports to
adapters. Contains no business logic.

### Core & Shared (`app/core`, `app/shared`)
Cross-cutting concerns used by every layer:
- `core/config.py` — typed, validated settings (Pydantic).
- `core/logging.py` — structured logging (structlog).
- `shared/exceptions` — the `DelphiError` hierarchy.
- `shared/utils` — dependency-free helpers.

> **Deliberate deviation from a "textbook" layout:** `config` and `logging` are placed in `core/`
> rather than `infrastructure/`. They are consumed by *every* layer including `main.py`
> (the composition root). Nesting them under `infrastructure` would imply inner layers depend on
> infrastructure — violating the dependency rule. `core/` is the standard home for framework-agnostic
> cross-cutting primitives.

## Dependency injection

FastAPI's `Depends` is our DI container. The pattern:

1. **Domain** declares an abstract port (`abc.ABC`).
2. **Infrastructure** implements it.
3. **`presentation/api/deps.py`** (composition root) constructs implementations from the
   long-lived objects on `app.state` and provides them to routers.

Because routers depend on *provider results*, not concrete classes, tests inject fakes via
`app.dependency_overrides` — see `tests/integration/test_health_endpoint.py`.

## Application lifecycle

`app/main.py` uses the ASGI **lifespan** protocol. On startup it constructs the `Database` and
`RedisCache` (which own connection pools) and stores them on `app.state`; on shutdown it disposes
them. This makes resource ownership explicit and leak-free.

## Request lifecycle & observability

`RequestContextMiddleware` (pure ASGI) assigns/propagates an `X-Request-ID`, binds it into the
structlog context so every log line for the request carries it, emits one structured access log,
and echoes the id in the response header. Logs render as coloured console output in development and
JSON in production (`DELPHI_LOG_FORMAT`).

## Error handling

Inner layers raise semantic errors (`DelphiError` subclasses: `NotFoundError`, `ValidationError`,
…) that carry a stable `code` and HTTP status. Centralised handlers in
`presentation/errors/handlers.py` map every failure — application errors, request validation, and
unexpected exceptions — into one JSON envelope:

```json
{ "error": { "code": "not_found", "message": "…", "details": {}, "request_id": "…" } }
```

## Health model (the reference vertical slice)

Health checking is implemented across all four layers to serve as a copyable template:

```
domain.HealthProbe (port) ─ implemented by ─ infrastructure.{Database,Redis}HealthProbe
         ▲                                              │
application.CheckSystemHealthUseCase ◀── deps.py wires ─┘
         ▲
presentation /api/v1/health  → 200 (ready) or 503 (unhealthy)
```

- `GET /health` — **liveness** (no I/O; unversioned for stable infra probes).
- `GET /api/v1/health` — **readiness** (probes datastores; versioned).

## API versioning

Business endpoints live under `/api/v1`. A future `v2` is added as a sibling router mounted in
parallel, so existing clients are never broken. Operational endpoints (`/`, `/health`) are
intentionally unversioned.

## Frontend architecture

The SPA is **feature-first**: shared primitives in `components/` and `lib/`, cross-cutting
providers in `app/providers`, and capabilities as self-contained modules under `features/`.
Server state is owned by **TanStack Query** via a typed API client (`services/api`); the app never
hand-rolls fetch/loading/error state. See [`frontend/README.md`](../frontend/README.md).

## Phase 2 — Identity, tenancy, and authorization

Phase 2 establishes the multi-tenant ownership model every future module inherits.

### Entity hierarchy

```
User ──▶ Membership ──▶ Organization ──▶ Workspace ──▶ Project ──▶ Dataset ──▶ DatasetVersion
```

| Entity | Purpose |
|--------|---------|
| **User** | Global identity; credentials live in infrastructure only |
| **Membership** | Links a user to an organization with a role |
| **Organization** | Top-level tenant boundary (billing, isolation) |
| **Workspace** | Collaboration partition within an org |
| **Project** | Unit of analytical work; datasets attach here |
| **RefreshToken** | Hashed, rotatable session continuity with reuse detection |
| **AuditLog** | Append-only security event trail |

See [docs/identity-and-tenancy.md](identity-and-tenancy.md) for the ERD, auth flow, RBAC matrix,
and API reference.

### Multi-tenancy strategy

Shared PostgreSQL with **row-level isolation** scoped by `organization_id`. Every tenant-aware
query receives a `TenantContext` (`user_id`, `organization_id`, `role`) resolved from the
`X-Organization-ID` header plus membership lookup. This avoids per-tenant databases while keeping
queries filterable and auditable.

### Authentication

- **Access tokens:** short-lived JWT (15 min default), sent as `Authorization: Bearer`.
- **Refresh tokens:** opaque, hashed in DB, rotated on each refresh; delivered as httpOnly cookie
  scoped to `/api/v1/auth` (SameSite=Lax; Secure in production).
- **Passwords:** Argon2id with validation (8–128 chars, letter + digit).
- **Rate limiting:** SlowAPI on auth endpoints (`DELPHI_AUTH_RATE_LIMIT`).
- **Future-ready:** OAuth, email verification, and password reset can plug in without refactoring
  the use-case layer.

### Authorization

Centralized in `application/authorization/authorization_service.py`. Roles: **Owner**, **Admin**,
**Analyst**, **Viewer**. Permission checks happen in use-cases via `require_permission()` — never
scattered in routers.

### API endpoints (v1)

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/refresh` | Cookie |
| POST | `/api/v1/auth/logout` | Optional bearer |
| GET | `/api/v1/auth/me` | Bearer |
| GET/POST | `/api/v1/organizations` | Bearer |
| GET/POST | `/api/v1/workspaces` | Bearer + `X-Organization-ID` |
| GET/POST | `/api/v1/projects` | Bearer + `X-Organization-ID` |

## Phase 3 — Dataset ingestion & lifecycle

Phase 3 introduces versioned tabular datasets scoped to projects. See
[docs/datasets.md](datasets.md) for the ERD, upload pipeline, storage layout, and API reference.

### Design highlights

- **DatasetVersion as analysis anchor** — future modules reference immutable version IDs.
- **StorageProvider port** — `LocalStorageProvider` today; S3/Azure/GCS without changing use-cases.
- **Polars profiling** — schema inference and preview sampling without loading full files.
- **UploadJob** — sync uploads today; same model supports async workers later.

### Dataset API endpoints (v1)

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/v1/datasets/upload` | Bearer + org + `dataset:create` |
| GET | `/api/v1/datasets?project_id=` | Bearer + org + `dataset:read` |
| GET | `/api/v1/datasets/{id}` | Bearer + org + `dataset:read` |
| GET | `/api/v1/datasets/{id}/versions` | Bearer + org + `dataset:read` |
| GET | `/api/v1/datasets/{id}/preview` | Bearer + org + `dataset:read` |
| DELETE | `/api/v1/datasets/{id}` | Bearer + org + `dataset:delete` |
| POST | `/api/v1/datasets/{id}/new-version` | Bearer + org + `dataset:update` |

All success responses use `{ "data": … }`. Run migrations before first use:

```bash
cd backend && uv run alembic upgrade head
```
