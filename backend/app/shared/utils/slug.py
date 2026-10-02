"""Generate URL-safe slugs from human-readable names."""

from __future__ import annotations

import re
import unicodedata


def slugify(value: str, *, max_length: int = 64) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:max_length] or "item"
