"""Unit tests for typed configuration parsing/validation."""

from __future__ import annotations

import pytest

from app.core.config import Environment, Settings

pytestmark = pytest.mark.unit

_PROD_DATABASE_URL = "postgresql+asyncpg://prod:strong_secret@db.example.com:5432/delphi"


def test_cors_origins_parsed_from_comma_separated_string() -> None:
    settings = Settings(cors_origins="http://a.com, http://b.com ,")  # type: ignore[arg-type]
    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_parsed_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    # Regression: pydantic-settings must not JSON-decode a comma-separated env
    # value for this list field (NoDecode + validator handle it).
    monkeypatch.setenv("DELPHI_CORS_ORIGINS", "http://a.com,http://b.com")
    settings = Settings()
    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_cors_origins_accepts_list() -> None:
    settings = Settings(cors_origins=["http://a.com"])
    assert settings.cors_origins == ["http://a.com"]


def test_is_production_flag() -> None:
    prod_settings = Settings(
        environment=Environment.PRODUCTION,
        debug=False,
        database_url=_PROD_DATABASE_URL,  # type: ignore[arg-type]
        jwt_secret_key="production_jwt_secret_with_sufficient_entropy",
    )
    assert prod_settings.is_production
    assert not Settings(environment=Environment.DEVELOPMENT).is_production


def test_database_and_redis_urls_are_strings() -> None:
    settings = Settings()
    assert settings.database_url_str.startswith("postgresql+asyncpg://")
    assert settings.redis_url_str.startswith("redis://")


def test_production_rejects_dev_database_credentials() -> None:
    with pytest.raises(ValueError, match="development credentials"):
        Settings(
            environment=Environment.PRODUCTION,
            database_url="postgresql+asyncpg://delphi:delphi_dev_password_change_me@localhost:5432/delphi",  # type: ignore[arg-type]
        )


def test_production_rejects_debug_mode() -> None:
    with pytest.raises(ValueError, match="DELPHI_DEBUG"):
        Settings(
            environment=Environment.PRODUCTION,
            debug=True,
            database_url=_PROD_DATABASE_URL,  # type: ignore[arg-type]
        )
