"""Causal inference API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DAGNodeRequest(BaseModel):
    id: str
    label: str
    role: str | None = None
    position: dict[str, float] | None = None


class DAGEdgeRequest(BaseModel):
    source: str
    target: str


class CreateDAGRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    nodes: list[DAGNodeRequest]
    edges: list[DAGEdgeRequest]
    variable_roles: dict[str, str] = Field(default_factory=dict)


class UpdateDAGRequest(CreateDAGRequest):
    pass


class CausalAnalyzeRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    dag_id: str | None = None
    treatment: str = Field(..., min_length=1)
    outcome: str = Field(..., min_length=1)
    business_question: str = Field(..., min_length=1)
    estimator: str | None = None
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    adjustment_set: list[str] | None = None
    run_refutation: bool = True
    run_sensitivity: bool = True


class CausalAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    dataset_id: str
    version_id: str
    dag_version_id: str | None = None
    status: str
    treatment: str
    outcome: str
    estimator: str | None = None
    error_message: str | None = None
    executed_at: str | None = None
    created_at: str
    result: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_entity(cls, run: Any) -> CausalAnalysisResponse:
        return cls(
            id=str(run.id),
            dataset_id=str(run.dataset_id),
            version_id=str(run.version_id),
            dag_version_id=str(run.dag_version_id) if run.dag_version_id else None,
            status=run.status.value if hasattr(run.status, "value") else run.status,
            treatment=run.treatment,
            outcome=run.outcome,
            estimator=run.estimator.value if run.estimator else None,
            error_message=run.error_message,
            executed_at=run.executed_at.isoformat() if run.executed_at else None,
            created_at=run.created_at.isoformat(),
            result=run.result or {},
        )


class DAGResponse(BaseModel):
    id: str
    dataset_id: str
    version_id: str
    name: str
    description: str | None = None
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    variable_roles: dict[str, str]
    version_number: int
    is_valid: bool
    validation_errors: list[str]
    created_at: str

    @classmethod
    def from_entity(cls, dag: Any) -> DAGResponse:
        return cls(
            id=str(dag.id),
            dataset_id=str(dag.dataset_id),
            version_id=str(dag.version_id),
            name=dag.name,
            description=dag.description,
            nodes=list(dag.nodes),
            edges=list(dag.edges),
            variable_roles=dict(dag.variable_roles),
            version_number=dag.version_number,
            is_valid=dag.is_valid,
            validation_errors=list(dag.validation_errors),
            created_at=dag.created_at.isoformat(),
        )


class CausalHistoryItem(BaseModel):
    id: str
    dataset_id: str
    version_id: str
    status: str
    treatment: str
    outcome: str
    estimator: str | None = None
    executed_at: str | None = None
    created_at: str

    @classmethod
    def from_entity(cls, run: Any) -> CausalHistoryItem:
        return cls(
            id=str(run.id),
            dataset_id=str(run.dataset_id),
            version_id=str(run.version_id),
            status=run.status.value if hasattr(run.status, "value") else run.status,
            treatment=run.treatment,
            outcome=run.outcome,
            estimator=run.estimator.value if run.estimator else None,
            executed_at=run.executed_at.isoformat() if run.executed_at else None,
            created_at=run.created_at.isoformat(),
        )
