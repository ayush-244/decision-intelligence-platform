"""Statistics API request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VariableSpecRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern="^(outcome|predictor|grouping|covariate|identifier)$")


class AnalyzeRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    goal: str = Field(..., min_length=1)
    research_question: str = Field(..., min_length=1)
    variables: list[VariableSpecRequest] = Field(..., min_length=1)
    test_type: str | None = None
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    reference_value: float | None = None


class RecommendationsRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    goal: str = Field(..., min_length=1)
    variables: list[VariableSpecRequest] = Field(..., min_length=1)


class AnalysisRunResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    dataset_id: str
    version_id: str
    status: str
    goal: str
    test_type: str | None = None
    research_question: str = ""
    error_message: str | None = None
    executed_at: str | None = None
    created_at: str
    result: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_entity(cls, run: Any) -> AnalysisRunResponse:
        config = run.configuration or {}
        return cls(
            id=str(run.id),
            dataset_id=str(run.dataset_id),
            version_id=str(run.version_id),
            status=run.status.value if hasattr(run.status, "value") else run.status,
            goal=run.goal,
            test_type=run.test_type.value if run.test_type else None,
            research_question=config.get("research_question", ""),
            error_message=run.error_message,
            executed_at=run.executed_at.isoformat() if run.executed_at else None,
            created_at=run.created_at.isoformat(),
            result=run.result or {},
        )


class AnalysisHistoryItem(BaseModel):
    id: str
    dataset_id: str
    version_id: str
    status: str
    goal: str
    test_type: str | None = None
    executed_at: str | None = None
    created_at: str

    @classmethod
    def from_entity(cls, run: Any) -> AnalysisHistoryItem:
        return cls(
            id=str(run.id),
            dataset_id=str(run.dataset_id),
            version_id=str(run.version_id),
            status=run.status.value if hasattr(run.status, "value") else run.status,
            goal=run.goal,
            test_type=run.test_type.value if run.test_type else None,
            executed_at=run.executed_at.isoformat() if run.executed_at else None,
            created_at=run.created_at.isoformat(),
        )
