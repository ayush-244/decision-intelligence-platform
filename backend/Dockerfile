# syntax=docker/dockerfile:1
# =============================================================================
# Decision Intelligence Platform backend — multi-stage build with uv.
#
# Stage 1 resolves and installs the *runtime* dependency set (no dev, no
# analytics extras) into a virtualenv using the frozen lockfile for
# reproducibility. Stage 2 is a slim runtime image containing only Python, the
# venv, and the application — run as a non-root user.
# =============================================================================

# ---- Stage 1: dependencies + app ------------------------------------------
FROM python:3.13-slim AS builder

# uv provides fast, deterministic installs from uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Install dependencies first (cached layer) without the project for better caching.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Now install the project itself.
COPY README.md ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- Stage 2: runtime ------------------------------------------------------
FROM python:3.13-slim AS runtime

# Create an unprivileged user to run the service.
RUN groupadd --system delphi && useradd --system --gid delphi --home /app delphi

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=builder --chown=delphi:delphi /app /app

USER delphi

EXPOSE 8000

# Liveness check hits the dependency-free /health endpoint using stdlib only.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
