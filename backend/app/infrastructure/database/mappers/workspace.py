"""Workspace entity mappers."""

from __future__ import annotations

from app.domain.entities.decision_session import DecisionSession
from app.domain.entities.session_activity import SessionActivity
from app.domain.value_objects.workspace import DecisionSessionStatus, SessionActivityType, WorkflowStep
from app.infrastructure.database.models.decision_session import (
    DecisionSessionModel,
    SessionActivityModel,
)


def to_decision_session(model: DecisionSessionModel) -> DecisionSession:
    return DecisionSession(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        created_by=model.created_by,
        name=model.name,
        description=model.description,
        status=DecisionSessionStatus(model.status),
        version_number=model.version_number,
        current_step=WorkflowStep(model.current_step),
        statistical_analysis_id=model.statistical_analysis_id,
        dag_version_id=model.dag_version_id,
        causal_analysis_id=model.causal_analysis_id,
        simulation_run_id=model.simulation_run_id,
        decision_run_id=model.decision_run_id,
        executive_report_id=model.executive_report_id,
        workspace_state=model.workspace_state_json,
        configuration=model.configuration_json,
        paused_at=model.paused_at,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_session_activity(model: SessionActivityModel) -> SessionActivity:
    return SessionActivity(
        id=model.id,
        session_id=model.session_id,
        organization_id=model.organization_id,
        user_id=model.user_id,
        activity_type=SessionActivityType(model.activity_type),
        title=model.title,
        description=model.description,
        resource_type=model.resource_type,
        resource_id=model.resource_id,
        metadata=model.metadata_json,
        created_at=model.created_at,
    )
