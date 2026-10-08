"""Load sampled Polars frames from stored dataset versions."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

import polars as pl

from app.core.config import Settings
from app.domain.entities.dataset_version import DatasetVersion
from app.domain.ports.storage_provider import StorageProvider
from app.domain.value_objects.data_source import DataSourceFormat
from app.shared.exceptions import BusinessValidationError


@dataclass(frozen=True, slots=True)
class SampledFrame:
    frame: pl.DataFrame
    total_rows: int
    sampled_rows: int
    was_sampled: bool


class DatasetFrameLoader:
    """Read version blobs via storage port with row caps for intelligence."""

    def __init__(self, settings: Settings, storage: StorageProvider) -> None:
        self._settings = settings
        self._storage = storage

    async def load(self, *, version: DatasetVersion) -> SampledFrame:
        data = await self._storage.read(key=version.storage_key)
        suffix = f".{version.source_format.value}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        try:
            return self._load_from_path(path=tmp_path, source_format=version.source_format)
        finally:
            tmp_path.unlink(missing_ok=True)

    def _load_from_path(self, *, path: Path, source_format: DataSourceFormat) -> SampledFrame:
        sample_cap = self._settings.intelligence_sample_rows

        if source_format is DataSourceFormat.CSV:
            lazy = pl.scan_csv(path, infer_schema_length=min(sample_cap, 1000))
            total_rows = int(lazy.select(pl.len()).collect().item())
            frame = lazy.head(sample_cap).collect()
        elif source_format is DataSourceFormat.PARQUET:
            lazy = pl.scan_parquet(path)
            total_rows = int(lazy.select(pl.len()).collect().item())
            frame = lazy.head(sample_cap).collect()
        elif source_format is DataSourceFormat.XLSX:
            frame = pl.read_excel(path)
            total_rows = frame.height
            if frame.height > sample_cap:
                frame = frame.head(sample_cap)
        else:
            raise BusinessValidationError(f"Unsupported format: {source_format}")

        if frame.height == 0 or frame.width == 0:
            raise BusinessValidationError("Dataset version contains no analyzable data.")

        sampled = frame.height
        return SampledFrame(
            frame=frame,
            total_rows=total_rows,
            sampled_rows=sampled,
            was_sampled=sampled < total_rows,
        )
