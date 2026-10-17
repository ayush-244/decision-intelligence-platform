"""Workspace DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkflowProgressDTO:
    current_step: str
    completed_steps: tuple[str, ...]
    total_steps: int
    percent_complete: float
    next_step: str | None


@dataclass(frozen=True, slots=True)
class TimelineEventDTO:
    id: str
    event_type: str
    title: str
    description: str | None
    resource_type: str | None
    resource_id: str | None
    occurred_at: str
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SearchResultDTO:
    resource_type: str
    resource_id: str
    title: str
    subtitle: str | None
    dataset_id: str | None
    created_at: str | None


@dataclass(frozen=True, slots=True)
class ComparisonItemDTO:
    label: str
    value_a: Any
    value_b: Any
    delta: Any | None
    highlight: bool


@dataclass(frozen=True, slots=True)
class SessionComparisonDTO:
    session_a_id: str
    session_b_id: str
    items: tuple[ComparisonItemDTO, ...]
    summary: str
