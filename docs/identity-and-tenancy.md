# Identity & Tenancy (Phase 2)

This document covers the domain model, authentication flow, authorization strategy, database
schema, and API surface introduced in Phase 2.

## Entity relationship diagram

```mermaid
erDiagram
    users ||--o{ organization_memberships : has
    organizations ||--o{ organization_memberships : has
    organizations ||--o{ workspaces : contains
    workspaces ||--o{ projects : contains
    users ||--o{ refresh_tokens : owns
    users ||--o{ audit_logs : triggers
    organizations ||--o{ audit_logs : scopes

    users {
        uuid id PK
        string email UK
        string password_hash
        string full_name
        bool is_active
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }

    organizations {
        uuid id PK
        string name
        string slug UK
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }

    organization_memberships {
        uuid id PK
        uuid user_id FK
        uuid organization_id FK
        string role
        bool is_active
        timestamptz created_at
        timestamptz updated_at
    }

    workspaces {
        uuid id PK
        uuid organization_id FK
        string name
        string slug
        text description
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }

    projects {
        uuid id PK
        uuid workspace_id FK
        string name
        string slug
        text description
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
    }

    refresh_tokens {
        uuid id PK
        uuid user_id FK
        string token_hash UK
        uuid family_id
        timestamptz expires_at
        timestamptz revoked_at
    }

    audit_logs {
        uuid id PK
        string action
        string resource_type
        uuid user_id FK
        uuid organization_id FK
        uuid resource_id
        jsonb metadata
        timestamptz created_at
    }
```

## Ownership rules

1. Every workspace belongs to exactly one organization.
2. Every project belongs to exactly one workspace (and therefore one organization).
3. Users access tenant resources only through active memberships.
4. Future datasets, analyses, and reports will attach to **projects** and inherit tenant scope.
5. Soft deletes (`deleted_at`) on users, organizations, workspaces, and projects preserve audit history.

## Database constraints

| Constraint | Rationale |
|------------|-----------|
| `uq_organization_memberships_user_org` | One membership row per user per org |
| `uq_workspaces_org_name` / `uq_workspaces_org_slug` | Unique workspace identity within org |
| `uq_projects_workspace_name` / `uq_projects_workspace_slug` | Unique project identity within workspace |
| `ON DELETE CASCADE` on membership/workspace/project FKs | Tear down child rows when parent is removed |
| `ON DELETE SET NULL` on audit log user/org FKs | Preserve logs after entity deletion |

Migration: `backend/migrations/versions/20250705180000_phase2_identity_tenancy.py`

## Authentication flow

```mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant DB as PostgreSQL

    C->>A: POST /auth/register
    A->>DB: Create user (Argon2 hash)
    A-->>C: 201 { data: user }

    C->>A: POST /auth/login
    A->>DB: Verify password, issue refresh token
    A-->>C: 200 { data: { user, tokens } } + httpOnly cookie

    C->>A: GET /auth/me (Bearer access token)
    A-->>C: 200 { data: user }

    C->>A: POST /auth/refresh (cookie)
    A->>DB: Rotate refresh token family
    A-->>C: 200 { data: { user, tokens } } + new cookie

    C->>A: POST /auth/logout
    A->>DB: Revoke refresh token
    A-->>C: 204 (cookie cleared)
```

**Token storage (frontend):** access token in `sessionStorage`; refresh token in httpOnly cookie.
The API client automatically retries once on `401` by calling `/auth/refresh`.

## Authorization strategy

RBAC is centralized in `AuthorizationService`. Roles and permissions:

| Role | Create org | Manage members | Workspace CRUD | Project CRUD | Read all |
|------|------------|----------------|----------------|--------------|----------|
| Owner | ✓ | ✓ | ✓ | ✓ | ✓ |
| Admin | — | ✓ | ✓ | ✓ | ✓ |
| Analyst | — | — | read | create/read | ✓ |
| Viewer | — | — | read | read | ✓ |

Tenant-scoped routes require:

1. Valid JWT (`Authorization: Bearer`)
2. Active membership for the org in `X-Organization-ID`

## Developer onboarding checklist

1. Copy `.env.example` → `.env` and set `DELPHI_JWT_SECRET_KEY`.
2. Start infrastructure: `docker compose up -d postgres redis`
3. Run migrations: `cd backend && uv run alembic upgrade head`
4. Start backend: `uv run uvicorn app.main:create_app --factory --reload`
5. Start frontend: `cd frontend && npm run dev`
6. Register at `http://localhost:5173/register`, create an organization, then workspaces/projects.

## Testing

- **Unit:** password hashing, authorization matrix (`tests/unit/`)
- **Integration:** full auth + tenancy flow with in-memory repositories (`tests/integration/test_auth_endpoints.py`)
- **Frontend:** login form render test (`frontend/src/pages/auth/login-page.test.tsx`)

Run all backend tests: `make test` or `cd backend && uv run pytest`
