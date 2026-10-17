"""Executive report entity mappers."""

from __future__ import annotations

from app.domain.entities.executive_report import ExecutiveReport
from app.domain.value_objects.executive import ExecutiveReportStatus
from app.infrastructure.database.models.executive_report import ExecutiveReportModel


def to_executive_report(model: ExecutiveReportModel) -> ExecutiveReport:
    return ExecutiveReport(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        decision_run_id=model.decision_run_id,
        created_by=model.created_by,  # type: ignore[arg-type]
        status=ExecutiveReportStatus(model.status),
        name=model.name,
        business_objective=model.business_objective,
        version_number=model.version_number,
        configuration=dict(model.configuration_json or {}),
        result=dict(model.result_json or {}),
        error_message=model.error_message,
        executed_at=model.executed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
