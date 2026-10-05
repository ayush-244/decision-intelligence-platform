"""Per-column schema metadata captured at ingest time."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.value_objects.column_type import ColumnSemanticType


@dataclass(frozen=True, slots=True)
class ColumnMetadata:
    name: str
    position: int
    semantic_type: ColumnSemanticType
    storage_type: str
    null_percentage: float
    distinct_count: int | None
    example_values: tuple[str, ...]
    type_confidence: float
