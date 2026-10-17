"""DTOs describing static service metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SystemInfo:
    """Immutable snapshot of service identity and build metadata."""

    name: str
    version: str
    environment: str
