# Roadmap

> **Phase 1 (engineering foundation), Phase 2 (identity & tenancy), Phase 3 (dataset lifecycle), and Phase 4 (data intelligence) are complete.**
> **Phase 5 (causal inference) is next.**

## Phase 1 — Engineering foundation ✅

- Clean Architecture modular monolith (backend) + feature-first SPA (frontend)
- Typed configuration, structured logging, centralised error handling
- Async PostgreSQL + Redis connection management with health probes
- Versioned API (`/`, `/health`, `/api/v1/health`, `/api/v1/version`)
- Docker + Compose (health-gated startup), GitHub Actions CI
- Ruff, Black, MyPy, Pytest, ESLint, Prettier, Vitest, pre-commit
- Documentation

## Phase 2 — Identity & workspaces ✅

- Authentication (JWT + refresh rotation), users, RBAC roles
- Organization / workspace / project hierarchy with multi-tenant isolation
- ORM models + Alembic migrations

## Phase 3 — Data ingestion & lifecycle ✅

- Versioned datasets (CSV, XLSX, Parquet) with schema inference and previews
- Storage abstraction (`LocalStorageProvider`; cloud-ready port)
- Polars-backed profiling pipeline; upload jobs for future async processing
- Dataset management UI with drag-and-drop upload and toast notifications

## Phase 4 — Data intelligence ✅

- Automated data quality and health scoring (explainable, modular)
- Column intelligence, missing data, outliers, correlations, distributions
- Analytical readiness assessment (regression, classification, clustering, causal)
- Intelligence report cached per DatasetVersion; ECharts-powered UI

## Phase 5 — Causal inference (next)

- Exploratory data analysis
- Descriptive & inferential statistics (hypothesis tests, correlations, effect sizes)

## Phase 5 — Causal inference

- Causal graph specification (DAGs)
- Effect estimation (adjustment, matching, IPW, DiD, IV) via Statsmodels/SciPy
- Assumption checks and sensitivity analysis — fully transparent

## Phase 6 — Counterfactual simulation

- "What if we change X?" intervention modelling
- Scenario comparison and uncertainty quantification

## Phase 7 — Recommendations

- Decision-science layer turning estimates into ranked, defensible actions
- Explicit assumptions, expected value, and risk

## Phase 8 — Reporting & explanation

- Executive reporting and interactive dashboards (Plotly / Apache ECharts)
- Natural-language explanation layer (LLM **explains** results; never replaces the math)

## Phase 9 — Operations

- Deployment (Vercel / Railway / Neon), monitoring, and observability hardening

> Design principle throughout: the analytical core stays statistically rigorous and transparent.
> LLMs are an explanation convenience, not a source of truth.
