"""Secrets provider port — abstracts env vars today, Vault tomorrow."""

from __future__ import annotations

from abc import ABC, abstractmethod


class SecretsProvider(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> str | None: ...

    @abstractmethod
    def require_secret(self, key: str) -> str: ...
