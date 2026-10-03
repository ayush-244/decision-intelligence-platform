"""Supported dataset file formats.

Kept as a value object so new connectors (JSON, JDBC, etc.) extend the enum
without changing ingestion contracts.
"""

from __future__ import annotations

from enum import StrEnum


class DataSourceFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    PARQUET = "parquet"

    @classmethod
    def from_filename(cls, filename: str) -> DataSourceFormat | None:
        lowered = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        mapping = {
            "csv": cls.CSV,
            "xlsx": cls.XLSX,
            "xls": cls.XLSX,
            "parquet": cls.PARQUET,
        }
        return mapping.get(lowered)

    @property
    def mime_types(self) -> frozenset[str]:
        return _MIME_TYPES[self]

    @property
    def extension(self) -> str:
        return _EXTENSIONS[self]


_MIME_TYPES: dict[DataSourceFormat, frozenset[str]] = {
    DataSourceFormat.CSV: frozenset({"text/csv", "application/csv", "text/plain"}),
    DataSourceFormat.XLSX: frozenset(
        {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        }
    ),
    DataSourceFormat.PARQUET: frozenset({"application/octet-stream", "application/x-parquet"}),
}

_EXTENSIONS: dict[DataSourceFormat, str] = {
    DataSourceFormat.CSV: "csv",
    DataSourceFormat.XLSX: "xlsx",
    DataSourceFormat.PARQUET: "parquet",
}
