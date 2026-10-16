"""Polars-based tabular file processing for schema inference and preview."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from app.core.config import Settings
from app.domain.entities.column_metadata import ColumnMetadata
from app.domain.value_objects.column_type import ColumnSemanticType
from app.domain.value_objects.data_source import DataSourceFormat
from app.shared.exceptions import BusinessValidationError


@dataclass(frozen=True, slots=True)
class TabularProfile:
    columns: tuple[ColumnMetadata, ...]
    row_count: int
    schema_hash: str
    preview_rows: list[dict[str, object]]


class TabularProcessor:
    """Infer schema and generate previews without loading full files into memory."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def profile_file(
        self,
        *,
        path: Path,
        source_format: DataSourceFormat,
    ) -> TabularProfile:
        sample_limit = self._settings.preview_sample_rows
        preview_limit = self._settings.preview_row_limit

        if source_format is DataSourceFormat.CSV:
            lazy = pl.scan_csv(path, infer_schema_length=min(sample_limit, 1000))
            sample = lazy.head(sample_limit).collect()
            row_count = lazy.select(pl.len()).collect().item()
        elif source_format is DataSourceFormat.PARQUET:
            lazy = pl.scan_parquet(path)
            sample = lazy.head(sample_limit).collect()
            row_count = lazy.select(pl.len()).collect().item()
        elif source_format is DataSourceFormat.XLSX:
            sample = pl.read_excel(path).head(sample_limit)
            row_count = sample.height
        else:
            raise BusinessValidationError(f"Unsupported format: {source_format}")

        if sample.height == 0 or sample.width == 0:
            raise BusinessValidationError("File contains no data.")

        columns = tuple(
            self._infer_column(sample, name, index) for index, name in enumerate(sample.columns)
        )
        schema_hash = self._hash_schema(columns)
        preview = sample.head(preview_limit).to_dicts()
        return TabularProfile(
            columns=columns,
            row_count=int(row_count),
            schema_hash=schema_hash,
            preview_rows=preview,
        )

    def _infer_column(self, frame: pl.DataFrame, name: str, position: int) -> ColumnMetadata:
        series = frame[name]
        total = frame.height
        null_count = series.null_count()
        null_pct = (null_count / total * 100.0) if total else 0.0
        non_null = series.drop_nulls()
        distinct_count = non_null.n_unique() if total else 0

        storage_type = str(series.dtype)
        semantic, confidence = self._semantic_type(series, distinct_count, total)

        examples: list[str] = []
        for value in non_null.head(5).to_list():
            examples.append(str(value))

        return ColumnMetadata(
            name=name,
            position=position,
            semantic_type=semantic,
            storage_type=storage_type,
            null_percentage=round(null_pct, 2),
            distinct_count=distinct_count,
            example_values=tuple(examples),
            type_confidence=confidence,
        )

    def _semantic_type(
        self,
        series: pl.Series,
        distinct_count: int,
        total: int,
    ) -> tuple[ColumnSemanticType, float]:
        dtype = series.dtype
        if dtype in {pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64}:
            if distinct_count == total and total > 0:
                return ColumnSemanticType.IDENTIFIER, 0.85
            return ColumnSemanticType.INTEGER, 0.95
        if dtype in {pl.Float32, pl.Float64}:
            return ColumnSemanticType.FLOAT, 0.95
        if dtype == pl.Boolean:
            return ColumnSemanticType.BOOLEAN, 0.95
        if dtype in {pl.Date, pl.Datetime, pl.Time}:
            return ColumnSemanticType.DATETIME, 0.9

        if dtype == pl.Utf8:
            if distinct_count <= min(50, max(1, total // 10)):
                return ColumnSemanticType.CATEGORICAL, 0.75
            return ColumnSemanticType.TEXT, 0.8

        return ColumnSemanticType.TEXT, 0.5

    def _hash_schema(self, columns: tuple[ColumnMetadata, ...]) -> str:
        payload = [
            {
                "name": col.name,
                "semantic_type": col.semantic_type.value,
                "storage_type": col.storage_type,
            }
            for col in columns
        ]
        encoded = json.dumps(payload, sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()
