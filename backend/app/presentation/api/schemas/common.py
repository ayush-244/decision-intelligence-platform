"""Standard API response envelopes."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    """Success envelope: ``{"data": ...}``."""

    data: T


class ListMeta(BaseModel):
    total: int = Field(ge=0)


class PaginatedDataResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: ListMeta
