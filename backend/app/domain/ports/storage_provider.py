"""Blob storage port — abstracts local disk, S3, Azure Blob, GCS, etc."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredObject:
    """Reference to a persisted blob."""

    key: str
    size_bytes: int


class StorageProvider(ABC):
    """Store and retrieve dataset artifacts without leaking filesystem details."""

    @abstractmethod
    async def store(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
    ) -> StoredObject: ...

    @abstractmethod
    async def store_stream(
        self,
        *,
        key: str,
        stream: AsyncIterator[bytes],
        content_type: str,
        expected_size: int | None = None,
    ) -> StoredObject: ...

    @abstractmethod
    async def read(self, *, key: str) -> bytes: ...

    @abstractmethod
    async def open_stream(self, *, key: str) -> AsyncIterator[bytes]: ...

    @abstractmethod
    async def delete(self, *, key: str) -> None: ...

    @abstractmethod
    async def exists(self, *, key: str) -> bool: ...

    async def health_check(self) -> None:
        """Verify storage backend is reachable. Override per adapter."""
        return None
