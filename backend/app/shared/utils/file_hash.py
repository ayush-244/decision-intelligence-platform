"""Content hashing for deduplication and integrity checks."""

from __future__ import annotations

import hashlib


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_streaming(chunks: list[bytes]) -> str:
    hasher = hashlib.sha256()
    for chunk in chunks:
        hasher.update(chunk)
    return hasher.hexdigest()
