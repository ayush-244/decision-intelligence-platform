"""Executive report endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Query

from app.presentation.api.deps import (
    ExportExecutiveReportDep,
    GenerateExecutiveReportDep,
    GetExecutiveDashboardDep,
    GetExecutiveReportDep,
    ListExecutiveReportsDep,
    TenantContextDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.executive import (
    ExecutiveReportHistoryItem,
    ExecutiveReportResponse,
    ExportReportRequest,
    GenerateReportRequest,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/generate",
    response_model=DataResponse[ExecutiveReportResponse],
    status_code=HTTPStatus.CREATED,
    summary="Generate an executive intelligence report",
)
async def generate_report(
    tenant: TenantContextDep,
    use_case: GenerateExecutiveReportDep,
    body: GenerateReportRequest,
) -> DataResponse[ExecutiveReportResponse]:
    report = await use_case.execute(
        tenant=tenant,
        dataset_id=UUID(body.dataset_id),
        decision_run_id=UUID(body.decision_run_id),
        name=body.name,
        business_objective=body.business_objective,
        version_id=UUID(body.version_id) if body.version_id else None,
        include_technical_appendix=body.include_technical_appendix,
    )
    return DataResponse(data=ExecutiveReportResponse.from_entity(report))


@router.get(
    "",
    response_model=DataResponse[list[ExecutiveReportHistoryItem]],
    summary="List executive reports for a dataset",
)
async def list_reports(
    tenant: TenantContextDep,
    use_case: ListExecutiveReportsDep,
    dataset_id: UUID = Query(...),
    limit: int = Query(default=50, ge=1, le=200),
) -> DataResponse[list[ExecutiveReportHistoryItem]]:
    reports = await use_case.execute(tenant=tenant, dataset_id=dataset_id, limit=limit)
    return DataResponse(data=[ExecutiveReportHistoryItem.from_entity(r) for r in reports])


@router.get(
    "/{report_id}",
    response_model=DataResponse[ExecutiveReportResponse],
    summary="Get an executive report by ID",
)
async def get_report(
    tenant: TenantContextDep,
    use_case: GetExecutiveReportDep,
    report_id: UUID,
) -> DataResponse[ExecutiveReportResponse]:
    report = await use_case.execute(tenant=tenant, report_id=report_id)
    return DataResponse(data=ExecutiveReportResponse.from_entity(report))


@router.post(
    "/export",
    response_model=DataResponse[dict],
    summary="Export an executive report",
)
async def export_report(
    tenant: TenantContextDep,
    use_case: ExportExecutiveReportDep,
    body: ExportReportRequest,
    report_id: UUID = Query(...),
) -> DataResponse[dict]:
    payload = await use_case.execute_export(
        tenant=tenant, report_id=report_id, format=body.format
    )
    return DataResponse(data=payload)
