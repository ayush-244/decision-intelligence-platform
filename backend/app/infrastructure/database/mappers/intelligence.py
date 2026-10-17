"""Map intelligence report ORM models to domain entities."""

from __future__ import annotations

from app.domain.entities.intelligence_report import IntelligenceReport
from app.domain.value_objects.intelligence_status import IntelligenceReportStatus
from app.infrastructure.database.models.intelligence_report import IntelligenceReportModel


def to_intelligence_report(model: IntelligenceReportModel) -> IntelligenceReport:
    return IntelligenceReport(
        id=model.id,
        dataset_id=model.dataset_id,
        version_id=model.version_id,
        organization_id=model.organization_id,
        status=IntelligenceReportStatus(model.status),
        quality_score=model.quality_score,
        health_score=model.health_score,
        rows_sampled=model.rows_sampled,
        total_rows=model.total_rows,
        report=dict(model.report_json),
        error_message=model.error_message,
        computed_at=model.computed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
