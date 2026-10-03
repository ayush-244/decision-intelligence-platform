"""Semantic column types inferred during schema detection.

Deliberately richer than raw Polars dtypes so downstream analytics can reason
about cardinality, ordinality, and identifiers without re-inference.
"""

from __future__ import annotations

from enum import StrEnum


class ColumnSemanticType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    DATETIME = "datetime"
    TEXT = "text"
    IDENTIFIER = "identifier"
    ORDINAL = "ordinal"  # reserved for future ordinal inference
