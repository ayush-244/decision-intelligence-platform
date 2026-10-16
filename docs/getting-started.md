# Getting started

Two supported workflows: **Docker** (fastest path to a running stack) and **native** (best for
day-to-day development with hot reload).

## 1. Docker (full stack)

### Prerequisites
- Docker + Docker Compose

### Steps
```bash
cp .env.example .env
docker compose up --build
```

Compose starts PostgreSQL and Redis, waits until they are **healthy**, then starts the backend and
frontend. Data persists in named volumes across restarts.

| Service | URL |
|---------|-----|
| Frontend (nginx) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Liveness | http://localhost:8000/health |
| Readiness | http://localhost:8000/api/v1/health |
| Version | http://localhost:8000/api/v1/version |
| API docs (debug only) | http://localhost:8000/docs |

Backend hot-reload is enabled automatically in development via
`docker-compose.override.yml` (source is mounted read-only and uvicorn runs with `--reload`).

```bash
docker compose down       # stop
docker compose down -v    # stop and wipe data volumes
docker compose logs -f    # tail logs
```

## 2. Native development

Run datastores in Docker but the apps on your host for the fastest feedback loop.

```bash
# Start only the datastores
docker compose up -d postgres redis
```

### Backend
Requires [uv](https://docs.astral.sh/uv/) and Python 3.13+.

```bash
cd backend
uv sync --all-extras     # runtime + dev (+ analytics extras)
uv run uvicorn app.main:app --reload
```

The backend reads configuration from the repo-root `.env` (see
[environment variables](environment-variables.md)).

### Frontend
Requires Node.js 20+ (22 recommended).

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev              # http://localhost:5173
```

## 3. Using the Makefile

From the repo root (`make help` lists everything):

```bash
make install        # backend + frontend deps
make hooks          # install pre-commit hooks
make dev-backend    # uvicorn --reload
make dev-frontend   # vite dev server
make lint           # all lint/type gates
make test           # backend tests
make up / make down # docker stack
```

## Troubleshooting

- **Backend can't reach the database** — ensure `postgres`/`redis` are up (`docker compose ps`) and
  that `DELPHI_DATABASE_URL` / `DELPHI_REDIS_URL` point at the right host (service names inside
  Compose, `localhost` when running natively).
- **Readiness returns 503** — one dependency is down; the JSON body lists which component and why.
- **Port already in use** — override `DELPHI_PORT`, `FRONTEND_PORT`, `POSTGRES_PORT`, or
  `REDIS_PORT` in `.env`.
