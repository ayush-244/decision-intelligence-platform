"""ROI calculation endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.deps import CalculateROIDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.simulation import ROIRequest

router = APIRouter(prefix="/roi", tags=["roi"])


@router.post(
    "",
    response_model=DataResponse[dict],
    summary="Calculate ROI from counterfactual outcomes",
)
async def calculate_roi(
    tenant: TenantContextDep,
    use_case: CalculateROIDep,
    body: ROIRequest,
) -> DataResponse[dict]:
    result = await use_case.execute(
        tenant=tenant,
        counterfactual=body.counterfactual,
        roi_assumptions=body.roi_assumptions,
    )
    return DataResponse(data=result)
