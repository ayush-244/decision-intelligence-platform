"""Intelligence API response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IntelligenceSectionResponse(BaseModel):
    """Flexible JSON section returned by intelligence slice endpoints."""

    model_config = ConfigDict(extra="allow")


class IntelligenceAnalyzeResponse(BaseModel):
    status: str
    quality_score: float | None
    health_score: float | None
    rows_sampled: int
    total_rows: int
    version_id: str
    computed_at: str | None = None


class IntelligenceReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    status: str
    quality_score: float | None = None
    health_score: float | None = None
    rows_sampled: int = 0
    total_rows: int = 0
    computed_at: str | None = None
    overview: dict[str, Any] = Field(default_factory=dict)
    data_quality: dict[str, Any] = Field(default_factory=dict)
    schema_summary: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)
    distributions: list[dict[str, Any]] = Field(default_factory=list)
    missing_data: dict[str, Any] = Field(default_factory=dict)
    outliers: dict[str, Any] = Field(default_factory=dict)
    correlations: dict[str, Any] = Field(default_factory=dict)
    feature_relationships: list[dict[str, Any]] = Field(default_factory=list)
    duplicates: dict[str, Any] = Field(default_factory=dict)
    data_health: dict[str, Any] = Field(default_factory=dict)
    analytical_readiness: dict[str, Any] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> IntelligenceReportResponse:
        return cls(**payload)
