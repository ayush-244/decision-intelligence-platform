"""Decision entity mappers."""

from __future__ import annotations

from app.domain.entities.decision_run import DecisionRun
from app.domain.value_objects.decision import DecisionRunStatus
from app.infrastructure.database.models.decision_run import DecisionRunModel


def to_decision_run(model: DecisionRunModel) -> DecisionRun:
    return DecisionRun(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        created_by=model.created_by,  # type: ignore[arg-type]
        status=DecisionRunStatus(model.status),
        name=model.name,
        primary_objective=model.primary_objective,
        configuration=dict(model.configuration_json or {}),
        result=dict(model.result_json or {}),
        error_message=model.error_message,
        executed_at=model.executed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
