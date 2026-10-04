"""The canonical error response envelope.

Every error returned by the API shares this shape, so clients can handle
failures uniformly and correlate them via ``request_id``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured error body."""

    code: str = Field(examples=["not_found"], description="Stable machine-readable code.")
    message: str = Field(description="Human-readable description.")
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = Field(default=None, description="Correlation id for this request.")


class ErrorResponse(BaseModel):
    """Top-level error envelope: ``{"error": {...}}``."""

    error: ErrorDetail
