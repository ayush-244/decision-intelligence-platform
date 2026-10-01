# =============================================================================
# Decision Intelligence Platform — developer task runner
# -----------------------------------------------------------------------------
# A single, discoverable entrypoint for common workflows so that a new engineer
# never has to memorise tool-specific invocations. Run `make help` for a list.
#
# Requires: make, uv, node/npm, docker. On Windows use Git Bash / WSL, or run
# the underlying commands directly (see docs/getting-started.md).
# =============================================================================

.DEFAULT_GOAL := help
SHELL := /bin/bash

BACKEND_DIR := backend
FRONTEND_DIR := frontend

## ----------------------------------------------------------------------------
## Meta
## ----------------------------------------------------------------------------
.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make <target>\n\nTargets:\n"} \
		/^[a-zA-Z0-9_.-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

## ----------------------------------------------------------------------------
## Setup
## ----------------------------------------------------------------------------
.PHONY: install
install: install-backend install-frontend ## Install all dependencies

.PHONY: install-backend
install-backend: ## Install backend dependencies (uv)
	cd $(BACKEND_DIR) && uv sync --all-extras

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies (npm)
	cd $(FRONTEND_DIR) && npm ci

.PHONY: hooks
hooks: ## Install git pre-commit hooks
	cd $(BACKEND_DIR) && uv run pre-commit install

## ----------------------------------------------------------------------------
## Run (local, without Docker)
## ----------------------------------------------------------------------------
.PHONY: dev-backend
dev-backend: ## Run the backend with autoreload
	cd $(BACKEND_DIR) && uv run uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000

.PHONY: dev-frontend
dev-frontend: ## Run the frontend dev server
	cd $(FRONTEND_DIR) && npm run dev

## ----------------------------------------------------------------------------
## Quality gates
## ----------------------------------------------------------------------------
.PHONY: lint
lint: lint-backend lint-frontend ## Lint everything

.PHONY: lint-backend
lint-backend: ## Ruff + Black (check) + MyPy
	cd $(BACKEND_DIR) && uv run ruff check . && uv run black --check . && uv run mypy app

.PHONY: lint-frontend
lint-frontend: ## ESLint + Prettier (check) + tsc
	cd $(FRONTEND_DIR) && npm run lint && npm run format:check && npm run typecheck

.PHONY: format
format: ## Auto-format backend and frontend
	cd $(BACKEND_DIR) && uv run ruff check --fix . && uv run black .
	cd $(FRONTEND_DIR) && npm run format

.PHONY: test
test: test-backend test-frontend ## Run all test suites

.PHONY: test-backend
test-backend: ## Run backend tests with coverage
	cd $(BACKEND_DIR) && uv run pytest

.PHONY: test-frontend
test-frontend: ## Run frontend unit tests
	cd $(FRONTEND_DIR) && npm run test

## ----------------------------------------------------------------------------
## Docker
## ----------------------------------------------------------------------------
.PHONY: up
up: ## Start the full stack (build if needed)
	docker compose up --build

.PHONY: down
down: ## Stop the stack and remove containers
	docker compose down

.PHONY: logs
logs: ## Tail logs for all services
	docker compose logs -f

.PHONY: clean
clean: ## Remove build artefacts and caches
	docker compose down -v --remove-orphans || true
	rm -rf $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/.ruff_cache $(BACKEND_DIR)/.mypy_cache
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/coverage
