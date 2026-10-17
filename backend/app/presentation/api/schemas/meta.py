"""Schemas for service metadata endpoints (root and version)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VersionResponse(BaseModel):
    """Service identity and build metadata."""

    name: str = Field(examples=["Delphi"])
    version: str = Field(examples=["0.1.0"])
    environment: str = Field(examples=["development"])


class RootResponse(BaseModel):
    """Welcome payload returned from the API root."""

    name: str = Field(examples=["Delphi"])
    tagline: str = Field(examples=["AI-Powered Decision Intelligence Platform"])
    version: str = Field(examples=["0.1.0"])
    docs_url: str | None = Field(default=None, examples=["/docs"])
