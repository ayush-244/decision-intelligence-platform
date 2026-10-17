"""Decision intelligence API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ObjectiveWeightRequest(BaseModel):
    objective: str
    weight: float = Field(ge=0.0, le=1.0)


class DecisionConstraintRequest(BaseModel):
    type: str
    severity: str = "soft"
    threshold: float | None = None
    description: str = ""


class DecisionAnalyzeRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    primary_objective: str = Field(..., min_length=1)
    simulation_run_ids: list[str] | None = None
    objective_weights: list[ObjectiveWeightRequest] | None = None
    constraints: list[DecisionConstraintRequest] | None = None
    risk_tolerance: float = Field(default=0.65, ge=0.0, le=1.0)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    max_budget: float | None = None


class DecisionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    dataset_id: str
    version_id: str
    status: str
    name: str
    primary_objective: str
    error_message: str | None = None
    executed_at: str | None = None
    created_at: str
    result: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_entity(cls, run: Any) -> DecisionResponse:
        return cls(
            id=str(run.id),
            dataset_id=str(run.dataset_id),
            version_id=str(run.version_id),
            status=run.status.value if hasattr(run.status, "value") else run.status,
            name=run.name,
            primary_objective=run.primary_objective,
            error_message=run.error_message,
            executed_at=run.executed_at.isoformat() if run.executed_at else None,
            created_at=run.created_at.isoformat(),
            result=run.result or {},
        )


class DecisionHistoryItem(BaseModel):
    id: str
    name: str
    status: str
    primary_objective: str
    created_at: str

    @classmethod
    def from_entity(cls, run: Any) -> DecisionHistoryItem:
        return cls(
            id=str(run.id),
            name=run.name,
            status=run.status.value if hasattr(run.status, "value") else run.status,
            primary_objective=run.primary_objective,
            created_at=run.created_at.isoformat(),
        )
