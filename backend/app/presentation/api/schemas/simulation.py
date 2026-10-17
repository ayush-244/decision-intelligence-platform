"""Simulation engine API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InterventionRequest(BaseModel):
    variable: str
    mode: str = "relative"
    value: float | str | bool
    reason: str | None = None


class ConstraintRequest(BaseModel):
    type: str
    severity: str = "soft"
    threshold: float | None = None
    description: str = ""
    value: float | None = None


class CreateScenarioRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    objective: str | None = None
    notes: str | None = None
    is_baseline: bool = False
    interventions: list[InterventionRequest]
    constraints: list[ConstraintRequest] = Field(default_factory=list)


class UpdateScenarioRequest(CreateScenarioRequest):
    pass


class RunSimulationRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    causal_analysis_id: str
    statistical_analysis_id: str | None = None
    scenario_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    objective: str = Field(..., min_length=1)
    interventions: list[InterventionRequest] | None = None
    constraints: list[ConstraintRequest] | None = None
    monte_carlo_iterations: int = Field(default=1000, ge=100, le=10000)
    confidence_level: float = Field(default=0.95, gt=0.0, lt=1.0)
    roi_assumptions: dict[str, Any] = Field(default_factory=dict)


class ROIRequest(BaseModel):
    counterfactual: dict[str, Any]
    roi_assumptions: dict[str, Any] = Field(default_factory=dict)


class RiskRequest(BaseModel):
    counterfactual: dict[str, Any]
    causal_result: dict[str, Any]
    constraints: list[ConstraintRequest] | None = None


class ScenarioResponse(BaseModel):
    id: str
    dataset_id: str
    version_id: str
    name: str
    description: str | None = None
    objective: str | None = None
    notes: str | None = None
    is_baseline: bool
    interventions: list[dict[str, Any]]
    constraints: list[dict[str, Any]]
    version_number: int
    parent_scenario_id: str | None = None
    created_at: str

    @classmethod
    def from_entity(cls, scenario: Any) -> ScenarioResponse:
        return cls(
            id=str(scenario.id),
            dataset_id=str(scenario.dataset_id),
            version_id=str(scenario.version_id),
            name=scenario.name,
            description=scenario.description,
            objective=scenario.objective,
            notes=scenario.notes,
            is_baseline=scenario.is_baseline,
            interventions=list(scenario.interventions),
            constraints=list(scenario.constraints),
            version_number=scenario.version_number,
            parent_scenario_id=str(scenario.parent_scenario_id) if scenario.parent_scenario_id else None,
            created_at=scenario.created_at.isoformat(),
        )


class SimulationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    dataset_id: str
    version_id: str
    causal_analysis_id: str
    statistical_analysis_id: str | None = None
    scenario_id: str
    status: str
    name: str
    error_message: str | None = None
    executed_at: str | None = None
    created_at: str
    result: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_entity(cls, run: Any) -> SimulationResponse:
        return cls(
            id=str(run.id),
            dataset_id=str(run.dataset_id),
            version_id=str(run.version_id),
            causal_analysis_id=str(run.causal_analysis_id),
            statistical_analysis_id=(
                str(run.statistical_analysis_id) if run.statistical_analysis_id else None
            ),
            scenario_id=str(run.scenario_id),
            status=run.status.value if hasattr(run.status, "value") else run.status,
            name=run.name,
            error_message=run.error_message,
            executed_at=run.executed_at.isoformat() if run.executed_at else None,
            created_at=run.created_at.isoformat(),
            result=run.result or {},
        )


class SimulationHistoryItem(BaseModel):
    id: str
    name: str
    status: str
    causal_analysis_id: str
    scenario_id: str
    created_at: str

    @classmethod
    def from_entity(cls, run: Any) -> SimulationHistoryItem:
        return cls(
            id=str(run.id),
            name=run.name,
            status=run.status.value if hasattr(run.status, "value") else run.status,
            causal_analysis_id=str(run.causal_analysis_id),
            scenario_id=str(run.scenario_id),
            created_at=run.created_at.isoformat(),
        )
