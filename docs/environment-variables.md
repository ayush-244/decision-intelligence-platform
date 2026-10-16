# Environment variables

All configuration is supplied via environment variables and validated at startup by
typed settings classes (Pydantic on the backend). The canonical template is
[`.env.example`](../.env.example) — copy it to `.env` and adjust.

> **Secrets are never committed.** Only `.env.example` is version-controlled. `.env` is git-ignored.

## Backend (`DELPHI_` prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `DELPHI_ENVIRONMENT` | `development` | `development` \| `staging` \| `production`. |
| `DELPHI_APP_NAME` | `Delphi` | Service name in logs & API metadata. |
| `DELPHI_DEBUG` | `false` | Enables interactive docs (`/docs`) and verbose errors. Keep `false` in production. |
| `DELPHI_LOG_LEVEL` | `INFO` | `DEBUG` \| `INFO` \| `WARNING` \| `ERROR` \| `CRITICAL`. |
| `DELPHI_LOG_FORMAT` | `console` | `json` for machine ingestion, `console` for local readability. |
| `DELPHI_HOST` | `0.0.0.0` | Bind address. |
| `DELPHI_PORT` | `8000` | Bind port. |
| `DELPHI_CORS_ORIGINS` | *(empty)* | Comma-separated list of allowed frontend origins. |
| `DELPHI_API_V1_PREFIX` | `/api/v1` | Mount prefix for versioned API. |
| `DELPHI_DATABASE_URL` | `postgresql+asyncpg://…` | Async SQLAlchemy DSN. |
| `DELPHI_REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL. |
| `DELPHI_JWT_SECRET_KEY` | *(dev default)* | Symmetric key for JWT access tokens. **Must be changed in production.** |
| `DELPHI_JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime. |
| `DELPHI_JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime. |
| `DELPHI_REFRESH_TOKEN_COOKIE_NAME` | `delphi_refresh_token` | httpOnly cookie name for refresh tokens. |
| `DELPHI_AUTH_RATE_LIMIT` | `10/minute` | SlowAPI rate limit for auth endpoints. |
| `DELPHI_STORAGE_BASE_PATH` | `./data/storage` | Root directory for uploaded dataset blobs (local provider). |
| `DELPHI_MAX_UPLOAD_SIZE_BYTES` | `104857600` | Maximum upload size (100 MiB default). |
| `DELPHI_PREVIEW_ROW_LIMIT` | `50` | Rows returned by the preview API. |
| `DELPHI_PREVIEW_SAMPLE_ROWS` | `10000` | Max rows scanned during schema inference. |

### PostgreSQL (consumed by docker-compose)

| Variable | Default |
|----------|---------|
| `POSTGRES_USER` | `delphi` |
| `POSTGRES_PASSWORD` | `delphi_dev_password_change_me` |
| `POSTGRES_DB` | `delphi` |
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432` |

### Redis (consumed by docker-compose)

| Variable | Default |
|----------|---------|
| `REDIS_HOST` | `localhost` |
| `REDIS_PORT` | `6379` |

## Frontend (`VITE_` prefix)

Only `VITE_`-prefixed variables are exposed to client code, and they are **inlined into the bundle
at build time** — never put secrets here.

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the backend API. |
| `VITE_APP_NAME` | `Delphi` | Display name. |

## How resolution works

- **Docker Compose** reads `.env` at the repo root and injects service-appropriate values (e.g. the
  backend's `DELPHI_DATABASE_URL` points at the `postgres` service name inside the Compose network).
- **Native backend** loads the repo-root `.env` via `pydantic-settings`.
- **Native frontend** loads `frontend/.env.local` via Vite.

Invalid or malformed configuration fails fast at startup rather than at first request.
