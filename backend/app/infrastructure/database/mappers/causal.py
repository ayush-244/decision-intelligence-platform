"""Map causal analysis ORM models to domain entities."""

from __future__ import annotations

from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.value_objects.causal import CausalEstimatorType, CausalRunStatus
from app.infrastructure.database.models.causal_analysis import CausalAnalysisRunModel


def to_causal_analysis_run(model: CausalAnalysisRunModel) -> CausalAnalysisRun:
    return CausalAnalysisRun(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        dag_version_id=model.dag_version_id,
        created_by=model.created_by,
        status=CausalRunStatus(model.status),
        treatment=model.treatment,
        outcome=model.outcome,
        estimator=CausalEstimatorType(model.estimator) if model.estimator else None,
        configuration=dict(model.configuration_json),
        result=dict(model.result_json),
        error_message=model.error_message,
        executed_at=model.executed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
