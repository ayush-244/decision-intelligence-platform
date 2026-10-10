"""DAGVersion — versioned causal directed acyclic graph."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DAGVersion:
    id: UUID
    dataset_id: UUID
    version_id: UUID
    organization_id: UUID
    project_id: UUID
    created_by: UUID
    name: str
    description: str | None
    nodes: tuple[dict[str, Any], ...]
    edges: tuple[dict[str, Any], ...]
    variable_roles: dict[str, str]
    version_number: int
    is_valid: bool
    validation_errors: tuple[str, ...]
    created_at: datetime
    updated_at: datetime
