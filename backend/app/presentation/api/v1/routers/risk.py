"""Risk assessment endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.deps import CalculateRiskDep, TenantContextDep
from app.presentation.api.schemas.common import DataResponse
from app.presentation.api.schemas.simulation import RiskRequest

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post(
    "",
    response_model=DataResponse[dict],
    summary="Assess intervention risk from counterfactual and causal model",
)
async def calculate_risk(
    tenant: TenantContextDep,
    use_case: CalculateRiskDep,
    body: RiskRequest,
) -> DataResponse[dict]:
    result = await use_case.execute(
        tenant=tenant,
        counterfactual=body.counterfactual,
        causal_result=body.causal_result,
        constraints=[c.model_dump() for c in body.constraints] if body.constraints else None,
    )
    return DataResponse(data=result)
