# Decision Intelligence Platform — Backend

FastAPI service implementing a **Clean Architecture modular monolith**. See the
repository root [`README.md`](../README.md) and [`docs/architecture.md`](../docs/architecture.md)
for the full picture; this file covers backend-local workflows.

## Layout

```
app/
  core/            # Cross-cutting: typed config, structured logging, constants
  shared/          # Exception hierarchy, dependency-free utils
  domain/          # Entities, value objects, repository interfaces (pure Python)
  application/     # Use-cases, application services, DTOs
  infrastructure/  # SQLAlchemy engine/session, Redis client, probe adapters
  presentation/    # FastAPI routers, middleware, schemas, error handlers, DI
  main.py          # App factory + ASGI lifespan (composition root)
migrations/        # Alembic (async) migration environment
tests/             # unit/ and integration/ suites
```

The dependency rule is enforced by convention and review: `domain` imports
nothing outward; `infrastructure` implements `domain` interfaces; `presentation`
wires everything together.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync --all-extras      # runtime + dev + analytics dependencies
uv run pre-commit install # optional: enable git hooks
```

## Run

```bash
# Requires PostgreSQL + Redis (use `docker compose up postgres redis` from root)
uv run uvicorn app.main:app --reload
```

- API root: <http://localhost:8000/>
- Liveness: <http://localhost:8000/health>
- Readiness: <http://localhost:8000/api/v1/health>
- Version: <http://localhost:8000/api/v1/version>
- Interactive docs (debug only): <http://localhost:8000/docs>

## Quality gates

```bash
uv run ruff check .        # lint + import order
uv run black --check .     # formatting
uv run mypy app            # strict static types
uv run pytest              # tests + coverage
```
