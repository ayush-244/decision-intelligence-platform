"""Local filesystem storage adapter."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from app.core.config import Settings
from app.domain.ports.storage_provider import StorageProvider, StoredObject
from app.shared.exceptions import NotFoundError


class LocalStorageProvider(StorageProvider):
    """Persist blobs under a configurable base directory on disk."""

    def __init__(self, settings: Settings) -> None:
        self._base = Path(settings.storage_base_path).resolve()
        self._base.mkdir(parents=True, exist_ok=True)

    def _resolve_key(self, key: str) -> Path:
        normalized = key.replace("\\", "/").lstrip("/")
        target = (self._base / normalized).resolve()
        if not str(target).startswith(str(self._base)):
            msg = "Invalid storage key: path traversal detected."
            raise ValueError(msg)
        return target

    async def store(self, *, key: str, data: bytes, content_type: str) -> StoredObject:
        del content_type
        path = self._resolve_key(key)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return StoredObject(key=key, size_bytes=len(data))

    async def store_stream(
        self,
        *,
        key: str,
        stream: AsyncIterator[bytes],
        content_type: str,
        expected_size: int | None = None,
    ) -> StoredObject:
        del content_type
        path = self._resolve_key(key)
        await asyncio.to_thread(path.parent.mkdir, parents=True, exist_ok=True)
        size = 0
        with path.open("wb") as handle:

            async def _write() -> None:
                nonlocal size
                async for chunk in stream:
                    handle.write(chunk)
                    size += len(chunk)

            await _write()
        if expected_size is not None and size != expected_size:
            await asyncio.to_thread(path.unlink, missing_ok=True)
            msg = f"Uploaded size {size} does not match expected {expected_size}."
            raise ValueError(msg)
        return StoredObject(key=key, size_bytes=size)

    async def read(self, *, key: str) -> bytes:
        path = self._resolve_key(key)
        if not path.is_file():
            raise NotFoundError("Stored object not found.")
        return await asyncio.to_thread(path.read_bytes)

    async def open_stream(self, *, key: str) -> AsyncIterator[bytes]:
        path = self._resolve_key(key)
        if not path.is_file():
            raise NotFoundError("Stored object not found.")
        data = await asyncio.to_thread(path.read_bytes)

        async def _gen() -> AsyncIterator[bytes]:
            yield data

        return _gen()

    async def delete(self, *, key: str) -> None:
        path = self._resolve_key(key)
        await asyncio.to_thread(path.unlink, missing_ok=True)

    async def exists(self, *, key: str) -> bool:
        path = self._resolve_key(key)
        return await asyncio.to_thread(path.is_file)

    async def health_check(self) -> None:
        exists = await asyncio.to_thread(self._base.exists)
        if not exists:
            raise OSError("Storage root is not accessible.")
