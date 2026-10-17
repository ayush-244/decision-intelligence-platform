<div align="center">

# Decision Intelligence Platform

### AI-Powered Causal Decision Intelligence Engine

*Traditional BI tells you **what happened**. Machine learning predicts **what will happen**.
This platform explains **why it happened**, **what you should do**, and **what happens if you change something**.*

</div>

---

The platform's intelligence comes from **statistics, causal inference, decision science, and business
analytics** — not from large language models. The core engine is statistically rigorous and
transparent by design. LLMs play a strictly supporting role: they explain analytical results in
plain language; they never produce the analysis itself.

> **Status: Phase 13 — AI Decision Copilot.** Structured context builder, replaceable LLM providers, tool routing, response validation, evidence citations, conversation persistence, and enterprise copilot workspace.
> See the [Roadmap](docs/roadmap.md).

## Table of contents

- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Repository structure](#repository-structure)
- [Getting started](#getting-started)
- [Development](#development)
- [Testing & quality](#testing--quality)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [License](#license)

## Architecture

The Decision Intelligence Platform is a **modular monolith** built with **Clean Architecture**. It is deployed as a single
service (no microservice overhead at this stage) but internally split into layers with a strict
inward-only dependency rule, so modules can be extracted later if scale ever demands it.

```
┌──────────────────────────────────────────────────────────┐
│ Presentation   FastAPI routers · middleware · schemas     │
│                exception handlers · dependency wiring      │
├──────────────────────────────────────────────────────────┤
│ Application    use-cases · application services · DTOs     │
├──────────────────────────────────────────────────────────┤
│ Domain         entities · value objects · repository ports │  ← knows no framework
├──────────────────────────────────────────────────────────┤
│ Infrastructure SQLAlchemy · asyncpg · Redis · adapters     │  → implements domain ports
├──────────────────────────────────────────────────────────┤
│ Core / Shared  config · logging · exceptions · utils        │  (cross-cutting)
└──────────────────────────────────────────────────────────┘
```

The full rationale — including why `config`/`logging` live in `core/` rather than
`infrastructure/`, and how dependency injection is wired — is in
[docs/architecture.md](docs/architecture.md).

## Tech stack

| Area | Choice |
|------|--------|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, TanStack Query, React Router, Framer Motion |
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, structlog |
| **Analytics engine** *(future)* | Polars, DuckDB, NumPy, SciPy, Statsmodels |
| **Datastores** | PostgreSQL 16, Redis 7 |
| **Infra & tooling** | Docker, Docker Compose, GitHub Actions, uv, Ruff, Black, MyPy, Pytest, ESLint, Prettier, Vitest, pre-commit |

## Repository structure

```
.
├── backend/            # FastAPI service (Clean Architecture) — see backend/README.md
├── frontend/           # React SPA (feature-first)          — see frontend/README.md
├── docs/               # Architecture, setup, env vars, roadmap
├── .github/workflows/  # CI: backend & frontend lint/test/build
├── docker-compose.yml  # Full local stack (+ override for dev hot-reload)
├── Makefile            # Discoverable developer task runner
└── .env.example        # Single source of truth for environment variables
```

## Getting started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- (For local, non-container development) [uv](https://docs.astral.sh/uv/) and Node.js 20+

### Run the whole stack with Docker (recommended)

```bash
cp .env.example .env          # adjust values as needed
docker compose up --build
cd backend && uv run alembic upgrade head   # apply Phase 2 schema
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (debug) | http://localhost:8000/docs |
| Readiness | http://localhost:8000/api/v1/health |

Full details, including running each side natively, are in
[docs/getting-started.md](docs/getting-started.md).

## Development

A `Makefile` provides a single, discoverable entrypoint (`make help`):

```bash
make install       # install backend (uv) + frontend (npm) deps
make hooks         # install pre-commit git hooks
make dev-backend   # uvicorn with autoreload
make dev-frontend  # Vite dev server
make lint          # lint backend + frontend
make test          # run backend tests
make up            # docker compose up --build
```

## Testing & quality

Quality gates are enforced locally (pre-commit) and in CI:

- **Backend:** Ruff (lint + import order), Black (format), MyPy (strict types), Pytest (+ coverage).
- **Frontend:** ESLint (type-aware), Prettier, `tsc` project references, Vitest.

```bash
make lint && make test          # backend + frontend gates
```

## Documentation

- [Architecture overview](docs/architecture.md)
- [Identity & tenancy (Phase 2)](docs/identity-and-tenancy.md)
- [Datasets & ingestion (Phase 3)](docs/datasets.md)
- [Data intelligence (Phase 4)](docs/data-intelligence.md)
- [Statistical analysis engine (Phase 5)](docs/statistics-engine.md)
- [Causal inference engine (Phase 6)](docs/causal-engine.md)
- [Decision simulation engine (Phase 7)](docs/simulation-engine.md)
- [Decision intelligence engine (Phase 8)](docs/decision-engine.md)
- [Executive intelligence layer (Phase 9)](docs/executive-intelligence.md)
- [Unified decision workspace (Phase 10)](docs/decision-workspace.md)
- [Enterprise infrastructure (Phase 11)](docs/infrastructure.md)
- [Caching strategy](docs/caching-strategy.md)
- [Security guide (Phase 12)](docs/security.md)
- [API governance](docs/api-governance.md)
- [Reliability guide](docs/reliability.md)
- [Observability guide](docs/observability.md)
- [Threat model](docs/threat-model.md)
- [Operational runbook](docs/operational-runbook.md)
- [AI Decision Copilot (Phase 13)](docs/copilot.md)
- [Getting started](docs/getting-started.md)
- [Environment variables](docs/environment-variables.md)
- [Roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)

## Roadmap

Foundation → Authentication → Workspaces → Dataset upload → Profiling → EDA → Statistical analysis →
Causal inference → Counterfactual simulation → Recommendations → Executive reporting → NL explanation.
See [docs/roadmap.md](docs/roadmap.md) for the sequenced plan.

## License

[MIT](LICENSE) © 2026 Ayush Kumar
