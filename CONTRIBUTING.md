# Contributing to Delphi

Thanks for contributing. This guide keeps the codebase consistent and reviewable as the team grows.

## Ground rules

- **Respect the architecture.** Dependencies point inward only
  (Presentation → Application → Domain; Infrastructure implements Domain ports). If you find
  yourself importing FastAPI/SQLAlchemy into `domain/`, stop and rethink. See
  [docs/architecture.md](docs/architecture.md).
- **Type everything.** Python is `mypy --strict`; TypeScript runs with strict `tsc`. No untyped
  public functions.
- **No placeholders in `main`.** Land working, tested code. Use feature branches for WIP.
- **SOLID, composition over inheritance, no magic numbers/strings** (use `core/constants.py` or a
  typed config), and no duplicated logic.

## Setup

```bash
make install     # backend (uv) + frontend (npm)
make hooks       # pre-commit git hooks
```

## Branch & commit

- Branch from `main`: `feat/…`, `fix/…`, `refactor/…`, `docs/…`, `chore/…`.
- Write clear, imperative commit messages explaining the **why**.
- Keep PRs focused and small enough to review well.

## Before you open a PR

Run the same gates CI runs:

```bash
make lint        # ruff + black + mypy  |  eslint + prettier + tsc
make test        # backend pytest
cd frontend && npm run test && npm run build
```

Pre-commit runs a subset automatically on `git commit`.

## Adding code

### Backend — a new use-case
1. Model concepts in `domain/` (entities/value objects, and a port if you need I/O).
2. Implement the port in `infrastructure/`.
3. Write the interactor in `application/use_cases/`.
4. Add a router + Pydantic schemas in `presentation/`, and wire dependencies in
   `presentation/api/deps.py`.
5. Add unit tests (domain/use-case) and an integration test (HTTP), using fakes for I/O.

### Backend — a new database model
1. Subclass `Base` in `infrastructure/database`.
2. Import the model in `migrations/env.py` so autogenerate detects it.
3. `uv run alembic revision --autogenerate -m "…"`, review the migration, commit it.

### Frontend — a new feature
Create `src/features/<feature>/` and co-locate its components, hooks, API bindings, and types.
Consume server state through TanStack Query hooks in `services/api`. Add shadcn/ui primitives with
`npx shadcn@latest add <component>`.

## Testing expectations

- New backend logic ships with tests; keep coverage from regressing.
- Prefer testing behaviour through public interfaces (HTTP routes, use-cases) over internals.
- Frontend: test user-visible behaviour with Testing Library.

## Code review

Every PR needs the checklist in the PR template satisfied and CI green before merge.
