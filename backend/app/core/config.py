"""Typed, validated application configuration.

Configuration is loaded once at import time from environment variables (and a
local ``.env`` for development) using ``pydantic-settings``. Two principles:

1. **Fail fast** — invalid or missing required configuration raises at startup,
   never at first request.
2. **Single source of truth** — every tunable is declared here with a type, a
   default where sensible, and validation. No module reads ``os.environ``
   directly.

All variables use the ``DELPHI_`` prefix to avoid collisions with unrelated
environment variables on shared hosts.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Repo root is two levels up from this file: backend/app/core/config.py
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Known weak defaults that must never reach production.
_DEV_DATABASE_PASSWORD = "delphi_dev_password_change_me"  # noqa: S105
_DEV_DATABASE_URL = f"postgresql+asyncpg://delphi:{_DEV_DATABASE_PASSWORD}@localhost:5432/delphi"


class Environment(StrEnum):
    """Deployment environment the process is running in."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogFormat(StrEnum):
    """Rendering strategy for structured log output."""

    JSON = "json"
    CONSOLE = "console"


class LogLevel(StrEnum):
    """Standard library logging levels, expressed as strings for config."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Application settings sourced from the environment.

    Attributes are grouped by concern. Every field is typed so that MyPy and
    Pydantic together guarantee the shape of configuration at runtime.
    """

    model_config = SettingsConfigDict(
        env_prefix="DELPHI_",
        env_file=(_REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---------------------------------------------------------
    app_name: str = Field(default="Delphi", description="Service name in logs/metadata.")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False, description="Enable interactive docs and verbose errors.")

    # --- Observability -------------------------------------------------------
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_format: LogFormat = Field(default=LogFormat.CONSOLE)

    # --- HTTP server ---------------------------------------------------------
    host: str = Field(default="0.0.0.0")  # noqa: S104 - binding is intentional for containers
    port: int = Field(default=8000, ge=1, le=65535)
    # NoDecode disables pydantic-settings' default JSON decoding for this field
    # so the validator below can accept a plain comma-separated env string.
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list)

    # --- API surface ---------------------------------------------------------
    api_v1_prefix: str = Field(default="/api/v1")

    # --- Datastores ----------------------------------------------------------
    database_url: PostgresDsn = Field(
        default=PostgresDsn(_DEV_DATABASE_URL),
        description="Async SQLAlchemy DSN (postgresql+asyncpg://...).",
    )
    redis_url: RedisDsn = Field(
        default=RedisDsn("redis://localhost:6379/0"),
        description="Redis connection URL.",
    )

    # --- Authentication (Phase 2) ------------------------------------------
    jwt_secret_key: str = Field(
        default="dev_jwt_secret_change_me_in_production",
        description="Symmetric key for signing JWT access tokens.",
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    jwt_refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    refresh_token_cookie_name: str = Field(default="delphi_refresh_token")
    auth_rate_limit: str = Field(
        default="10/minute",
        description="Rate limit string for auth endpoints (slowapi format).",
    )

    # --- Dataset storage (Phase 3) -------------------------------------------
    storage_base_path: Path = Field(
        default=_REPO_ROOT / "data" / "storage",
        description="Root directory for dataset blob storage (local adapter).",
    )
    max_upload_size_bytes: int = Field(
        default=104_857_600,
        ge=1,
        description="Maximum upload size in bytes (default 100 MiB).",
    )
    preview_row_limit: int = Field(default=50, ge=1, le=500)
    preview_sample_rows: int = Field(
        default=10_000,
        ge=100,
        description="Max rows scanned for schema inference (streaming cap).",
    )

    # --- Data intelligence (Phase 4) -----------------------------------------
    intelligence_sample_rows: int = Field(
        default=100_000,
        ge=1_000,
        description="Max rows sampled for intelligence profiling.",
    )
    intelligence_correlation_max_columns: int = Field(
        default=30,
        ge=2,
        le=100,
        description="Max numeric columns in correlation matrix.",
    )
    outlier_zscore_threshold: float = Field(
        default=3.0,
        ge=2.0,
        le=5.0,
        description="Z-score threshold for outlier flagging.",
    )

    # --- Statistical analysis (Phase 5) --------------------------------------
    statistics_significance_level: float = Field(
        default=0.05,
        gt=0.0,
        lt=1.0,
        description="Alpha level for hypothesis tests.",
    )
    statistics_confidence_level: float = Field(
        default=0.95,
        gt=0.0,
        lt=1.0,
        description="Default confidence level for intervals.",
    )
    statistics_sample_rows: int = Field(
        default=100_000,
        ge=1_000,
        description="Max rows sampled for statistical analysis.",
    )

    # --- Enterprise infrastructure (Phase 11) --------------------------------
    worker_enabled: bool = Field(
        default=False,
        description="Start background worker in application lifespan.",
    )
    worker_poll_interval_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Background worker queue poll interval.",
    )
    job_max_retries: int = Field(default=3, ge=0, le=10)
    slow_query_threshold_ms: float = Field(
        default=500.0,
        ge=50.0,
        description="Threshold for slow query detection metrics.",
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable analytics result caching via Redis.",
    )

    # --- Production hardening (Phase 12) -------------------------------------
    api_rate_limit: str = Field(
        default="200/minute",
        description="Global API rate limit (slowapi format).",
    )
    max_request_body_bytes: int = Field(
        default=10_485_760,
        ge=1024,
        description="Maximum HTTP request body size (default 10 MiB).",
    )
    idempotency_enabled: bool = Field(default=True)
    idempotency_ttl_seconds: int = Field(default=86_400, ge=60, le=604_800)
    circuit_breaker_failure_threshold: int = Field(default=5, ge=1, le=50)
    circuit_breaker_recovery_seconds: float = Field(default=30.0, ge=5.0, le=600.0)

    # --- AI Decision Copilot (Phase 13) --------------------------------------
    llm_provider: str = Field(default="mock", description="LLM provider: mock, openai, anthropic, etc.")
    llm_model: str = Field(default="gpt-4o-mini")
    llm_base_url: str = Field(default="https://api.openai.com/v1")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key when provider=openai.")
    copilot_max_tokens: int = Field(default=2048, ge=256, le=8192)

    @property
    def quality_score_weights(self) -> dict[str, float]:
        return {
            "completeness": 0.25,
            "uniqueness": 0.15,
            "consistency": 0.20,
            "validity": 0.20,
            "integrity": 0.20,
        }

    @property
    def health_score_weights(self) -> dict[str, float]:
        return {
            "data_quality": 0.30,
            "missingness": 0.20,
            "outliers": 0.15,
            "column_usability": 0.15,
            "distributions": 0.10,
            "cardinality": 0.10,
        }

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string (env-friendly) or a real list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _validate_production_safety(self) -> Settings:
        """Reject known-weak configuration in non-development environments."""
        if self.environment is Environment.DEVELOPMENT:
            return self

        url = self.database_url_str
        if _DEV_DATABASE_PASSWORD in url or url == _DEV_DATABASE_URL:
            msg = "Production database URL must not use development credentials."
            raise ValueError(msg)

        if self.environment is Environment.PRODUCTION and self.debug:
            msg = "DELPHI_DEBUG must be false in production."
            raise ValueError(msg)

        if self.environment is Environment.PRODUCTION and self.jwt_secret_key.startswith("dev_jwt"):
            msg = "Production JWT secret must be replaced with a strong random value."
            raise ValueError(msg)

        return self

    @property
    def is_production(self) -> bool:
        """True when running under the production environment."""
        return self.environment is Environment.PRODUCTION

    @property
    def database_url_str(self) -> str:
        """DSN as a plain string for SQLAlchemy engine creation."""
        return str(self.database_url)

    @property
    def redis_url_str(self) -> str:
        """Redis URL as a plain string for client creation."""
        return str(self.redis_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    Cached so the ``.env`` file and environment are parsed exactly once. Tests
    can clear the cache via ``get_settings.cache_clear()`` to inject overrides.
    """
    return Settings()
