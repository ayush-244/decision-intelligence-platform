"""Dataset ingestion and lifecycle endpoints."""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.presentation.api.deps import (
    AnalyzeDatasetIntelligenceDep,
    DeleteDatasetDep,
    GetDatasetColumnsIntelligenceDep,
    GetDatasetCorrelationsDep,
    GetDatasetDep,
    GetDatasetIntelligenceDep,
    GetDatasetIntelligenceSummaryDep,
    GetDatasetMissingDep,
    GetDatasetOutliersDep,
    GetDatasetPreviewDep,
    GetDatasetQualityDep,
    ListDatasetVersionsDep,
    ListDatasetsDep,
    TenantContextDep,
    UploadDatasetDep,
    UploadDatasetVersionDep,
)
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.dataset import (
    DatasetPreviewResponse,
    DatasetResponse,
    DatasetVersionResponse,
    UploadResultResponse,
)
from app.presentation.api.schemas.intelligence import (
    IntelligenceAnalyzeResponse,
    IntelligenceReportResponse,
    IntelligenceSectionResponse,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post(
    "/upload",
    response_model=DataResponse[UploadResultResponse],
    status_code=HTTPStatus.CREATED,
    summary="Upload a new dataset to a project",
)
async def upload_dataset(
    tenant: TenantContextDep,
    use_case: UploadDatasetDep,
    project_id: UUID = Form(...),
    file: UploadFile = File(...),
    name: str | None = Form(default=None),
    description: str | None = Form(default=None),
) -> DataResponse[UploadResultResponse]:
    data = await file.read()
    result = await use_case.execute(
        tenant=tenant,
        project_id=project_id,
        filename=file.filename or "upload.csv",
        content_type=file.content_type,
        data=data,
        name=name,
        description=description,
    )
    return DataResponse(data=UploadResultResponse.from_dto(result))


@router.get(
    "",
    response_model=DataResponse[list[DatasetResponse]],
    summary="List datasets in a project",
)
async def list_datasets(
    tenant: TenantContextDep,
    use_case: ListDatasetsDep,
    project_id: UUID = Query(..., description="Project to list datasets from"),
) -> DataResponse[list[DatasetResponse]]:
    rows = await use_case.execute(tenant=tenant, project_id=project_id)
    return DataResponse(data=[DatasetResponse.from_dto(row) for row in rows])


@router.get(
    "/{dataset_id}",
    response_model=DataResponse[DatasetResponse],
    summary="Get dataset details",
)
async def get_dataset(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetDep,
) -> DataResponse[DatasetResponse]:
    dataset = await use_case.execute(tenant=tenant, dataset_id=dataset_id)
    return DataResponse(data=DatasetResponse.from_dto(dataset))


@router.get(
    "/{dataset_id}/versions",
    response_model=DataResponse[list[DatasetVersionResponse]],
    summary="List all versions of a dataset",
)
async def list_dataset_versions(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: ListDatasetVersionsDep,
) -> DataResponse[list[DatasetVersionResponse]]:
    rows = await use_case.execute(tenant=tenant, dataset_id=dataset_id)
    return DataResponse(data=[DatasetVersionResponse.from_dto(row) for row in rows])


@router.get(
    "/{dataset_id}/preview",
    response_model=DataResponse[DatasetPreviewResponse],
    summary="Preview dataset rows and schema",
)
async def preview_dataset(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetPreviewDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[DatasetPreviewResponse]:
    preview = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=DatasetPreviewResponse.from_dto(preview))


@router.delete(
    "/{dataset_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Soft-delete a dataset",
)
async def delete_dataset(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: DeleteDatasetDep,
) -> None:
    await use_case.execute(tenant=tenant, dataset_id=dataset_id)


@router.post(
    "/{dataset_id}/new-version",
    response_model=DataResponse[UploadResultResponse],
    status_code=HTTPStatus.CREATED,
    summary="Upload a new version of an existing dataset",
)
async def upload_new_version(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: UploadDatasetVersionDep,
    file: UploadFile = File(...),
) -> DataResponse[UploadResultResponse]:
    data = await file.read()
    result = await use_case.execute(
        tenant=tenant,
        dataset_id=dataset_id,
        filename=file.filename or "upload.csv",
        content_type=file.content_type,
        data=data,
    )
    return DataResponse(data=UploadResultResponse.from_dto(result))


@router.post(
    "/{dataset_id}/intelligence/analyze",
    response_model=DataResponse[IntelligenceAnalyzeResponse],
    status_code=HTTPStatus.CREATED,
    summary="Run data intelligence analysis on a dataset version",
)
async def analyze_dataset_intelligence(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: AnalyzeDatasetIntelligenceDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceAnalyzeResponse]:
    report = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(
        data=IntelligenceAnalyzeResponse(
            status=report.status.value,
            quality_score=report.quality_score,
            health_score=report.health_score,
            rows_sampled=report.rows_sampled,
            total_rows=report.total_rows,
            version_id=str(report.version_id),
            computed_at=report.computed_at.isoformat() if report.computed_at else None,
        )
    )


@router.get(
    "/{dataset_id}/intelligence",
    response_model=DataResponse[IntelligenceReportResponse],
    summary="Get the full data intelligence report",
)
async def get_dataset_intelligence(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetIntelligenceDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceReportResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=IntelligenceReportResponse.from_payload(payload))


@router.get(
    "/{dataset_id}/quality",
    response_model=DataResponse[IntelligenceSectionResponse],
    summary="Get data quality metrics and score",
)
async def get_dataset_quality(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetQualityDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceSectionResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=IntelligenceSectionResponse(**payload))


@router.get(
    "/{dataset_id}/columns",
    response_model=DataResponse[IntelligenceSectionResponse],
    summary="Get per-column intelligence metadata",
)
async def get_dataset_columns_intelligence(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetColumnsIntelligenceDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceSectionResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=IntelligenceSectionResponse(**payload))


@router.get(
    "/{dataset_id}/correlations",
    response_model=DataResponse[IntelligenceSectionResponse],
    summary="Get correlation analysis",
)
async def get_dataset_correlations(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetCorrelationsDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceSectionResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=IntelligenceSectionResponse(**payload))


@router.get(
    "/{dataset_id}/outliers",
    response_model=DataResponse[IntelligenceSectionResponse],
    summary="Get outlier detection results",
)
async def get_dataset_outliers(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetOutliersDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceSectionResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=IntelligenceSectionResponse(**payload))


@router.get(
    "/{dataset_id}/missing",
    response_model=DataResponse[IntelligenceSectionResponse],
    summary="Get missing data analysis",
)
async def get_dataset_missing(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetMissingDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceSectionResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=IntelligenceSectionResponse(**payload))


@router.get(
    "/{dataset_id}/summary",
    response_model=DataResponse[IntelligenceSectionResponse],
    summary="Get intelligence summary dashboard data",
)
async def get_dataset_intelligence_summary(
    dataset_id: UUID,
    tenant: TenantContextDep,
    use_case: GetDatasetIntelligenceSummaryDep,
    version_id: UUID | None = Query(default=None),
) -> DataResponse[IntelligenceSectionResponse]:
    payload = await use_case.execute(
        tenant=tenant, dataset_id=dataset_id, version_id=version_id
    )
    return DataResponse(data=IntelligenceSectionResponse(**payload))
