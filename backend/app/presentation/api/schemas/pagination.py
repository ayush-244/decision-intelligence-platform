"""Standard pagination query parameters and response metadata."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class SortParams(BaseModel):
    sort_by: str | None = Field(default=None, max_length=64)
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
