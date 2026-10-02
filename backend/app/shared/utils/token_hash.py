"""Hash opaque tokens for storage (refresh tokens)."""

from __future__ import annotations

import hashlib


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
