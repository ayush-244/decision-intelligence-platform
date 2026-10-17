"""Map statistical analysis ORM models to domain entities."""

from __future__ import annotations

from app.domain.entities.statistical_analysis import StatisticalAnalysisRun
from app.domain.value_objects.statistics import AnalysisRunStatus, StatisticalTestType
from app.infrastructure.database.models.statistical_analysis import StatisticalAnalysisRunModel


def to_statistical_analysis_run(model: StatisticalAnalysisRunModel) -> StatisticalAnalysisRun:
    return StatisticalAnalysisRun(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        project_id=model.project_id,
        created_by=model.created_by,
        status=AnalysisRunStatus(model.status),
        goal=model.goal,
        test_type=StatisticalTestType(model.test_type) if model.test_type else None,
        configuration=dict(model.configuration_json),
        result=dict(model.result_json),
        error_message=model.error_message,
        executed_at=model.executed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
