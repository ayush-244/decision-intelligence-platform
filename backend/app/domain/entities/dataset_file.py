"""DatasetFile — physical file metadata for a version.

Separates logical version metadata from the on-disk artifact so multi-file
sources (e.g. partitioned Parquet) can be added without schema changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DatasetFile:
    id: UUID
    version_id: UUID
    original_filename: str
    sanitized_filename: str
    mime_type: str
    file_size_bytes: int
    file_hash: str
    storage_key: str
    created_at: datetime
