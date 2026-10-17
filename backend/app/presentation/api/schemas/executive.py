"""Executive report API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GenerateReportRequest(BaseModel):
    dataset_id: str
    version_id: str | None = None
    decision_run_id: str
    name: str = Field(..., min_length=1, max_length=255)
    business_objective: str = Field(..., min_length=1)
    include_technical_appendix: bool = False


class ExportReportRequest(BaseModel):
    format: str = Field(default="markdown", pattern="^(markdown|csv|json|pdf)$")


class ExecutiveReportResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    dataset_id: str
    version_id: str
    decision_run_id: str | None = None
    status: str
    name: str
    business_objective: str
    version_number: int
    error_message: str | None = None
    executed_at: str | None = None
    created_at: str
    result: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_entity(cls, report: Any) -> ExecutiveReportResponse:
        return cls(
            id=str(report.id),
            dataset_id=str(report.dataset_id),
            version_id=str(report.version_id),
            decision_run_id=str(report.decision_run_id) if report.decision_run_id else None,
            status=report.status.value if hasattr(report.status, "value") else report.status,
            name=report.name,
            business_objective=report.business_objective,
            version_number=report.version_number,
            error_message=report.error_message,
            executed_at=report.executed_at.isoformat() if report.executed_at else None,
            created_at=report.created_at.isoformat(),
            result=report.result or {},
        )


class ExecutiveReportHistoryItem(BaseModel):
    id: str
    name: str
    status: str
    version_number: int
    created_at: str

    @classmethod
    def from_entity(cls, report: Any) -> ExecutiveReportHistoryItem:
        return cls(
            id=str(report.id),
            name=report.name,
            status=report.status.value if hasattr(report.status, "value") else report.status,
            version_number=report.version_number,
            created_at=report.created_at.isoformat(),
        )
