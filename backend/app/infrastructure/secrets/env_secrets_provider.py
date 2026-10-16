"""Environment-variable secrets provider (default for all deployments)."""

from __future__ import annotations

import os

from app.shared.exceptions import ServiceUnavailableError


class EnvSecretsProvider:
    """Reads secrets from process environment with DELPHI_ prefix convention."""

    def __init__(self, *, prefix: str = "DELPHI_") -> None:
        self._prefix = prefix

    def get_secret(self, key: str) -> str | None:
        env_key = key if key.startswith(self._prefix) else f"{self._prefix}{key.upper()}"
        return os.environ.get(env_key)

    def require_secret(self, key: str) -> str:
        value = self.get_secret(key)
        if value is None or not value.strip():
            raise ServiceUnavailableError(
                f"Required secret '{key}' is not configured.",
                code="secret_missing",
            )
        return value
