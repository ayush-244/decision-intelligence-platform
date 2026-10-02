"""Sanitize user-supplied filenames for safe storage."""

from __future__ import annotations

import re
import uuid
from pathlib import PurePosixPath

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str, *, max_length: int = 200) -> str:
    """Strip path components and unsafe characters; preserve extension."""
    base = PurePosixPath(filename).name
    if not base or base in {".", ".."}:
        base = "upload"
    stem = PurePosixPath(base).stem
    suffix = PurePosixPath(base).suffix.lower()
    safe_stem = _UNSAFE.sub("_", stem).strip("._") or "file"
    safe_stem = safe_stem[: max_length - len(suffix)]
    return f"{safe_stem}{suffix}" if suffix else safe_stem


def unique_storage_filename(filename: str) -> str:
    """Append a short unique suffix before the extension."""
    sanitized = sanitize_filename(filename)
    path = PurePosixPath(sanitized)
    token = uuid.uuid4().hex[:8]
    if path.suffix:
        return f"{path.stem}_{token}{path.suffix}"
    return f"{sanitized}_{token}"
