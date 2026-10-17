"""Simulation entity mappers."""

from __future__ import annotations

from app.domain.entities.simulation_run import SimulationRun
from app.domain.entities.simulation_scenario import SimulationScenario
from app.domain.value_objects.simulation import SimulationRunStatus
from app.infrastructure.database.models.simulation_run import SimulationRunModel
from app.infrastructure.database.models.simulation_scenario import SimulationScenarioModel


def to_simulation_scenario(model: SimulationScenarioModel) -> SimulationScenario:
    return SimulationScenario(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        created_by=model.created_by,  # type: ignore[arg-type]
        name=model.name,
        description=model.description,
        objective=model.objective,
        notes=model.notes,
        is_baseline=model.is_baseline,
        interventions=list(model.interventions_json or []),
        constraints=list(model.constraints_json or []),
        version_number=model.version_number,
        parent_scenario_id=model.parent_scenario_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_simulation_run(model: SimulationRunModel) -> SimulationRun:
    return SimulationRun(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        causal_analysis_id=model.causal_analysis_id,
        statistical_analysis_id=model.statistical_analysis_id,
        scenario_id=model.scenario_id,
        created_by=model.created_by,  # type: ignore[arg-type]
        status=SimulationRunStatus(model.status),
        name=model.name,
        configuration=dict(model.configuration_json or {}),
        result=dict(model.result_json or {}),
        error_message=model.error_message,
        executed_at=model.executed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
