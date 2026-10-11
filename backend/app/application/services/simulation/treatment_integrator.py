"""Integrate Phase 6 causal treatment effects into simulation."""

from __future__ import annotations

from typing import Any

from app.application.dto.causal import TreatmentEffectDTO
from app.domain.entities.causal_analysis import CausalAnalysisRun
from app.domain.value_objects.causal import CausalEstimatorType, CausalRunStatus
from app.shared.exceptions import BusinessValidationError


class TreatmentEffectIntegrator:
    """Extract and validate treatment effects from completed causal analyses."""

    def extract(self, causal_run: CausalAnalysisRun) -> TreatmentEffectDTO:
        if causal_run.status is not CausalRunStatus.COMPLETED:
            raise BusinessValidationError(
                "Causal analysis must be completed before simulation.",
                code="causal_not_completed",
            )
        te_data: dict[str, Any] = causal_run.result.get("treatment_effect", {})
        if not te_data:
            raise BusinessValidationError(
                "Causal analysis has no treatment effect estimate.",
                code="missing_treatment_effect",
            )
        estimator_raw = te_data.get("estimator") or causal_run.estimator
        estimator = (
            CausalEstimatorType(estimator_raw)
            if isinstance(estimator_raw, str)
            else estimator_raw or CausalEstimatorType.DIFFERENCE_IN_MEANS
        )
        return TreatmentEffectDTO(
            estimator=estimator,
            ate=te_data.get("ate"),
            att=te_data.get("att"),
            atc=te_data.get("atc"),
            std_error=te_data.get("std_error"),
            confidence_level=te_data.get("confidence_level", 0.95),
            ci_lower=te_data.get("ci_lower"),
            ci_upper=te_data.get("ci_upper"),
            p_value=te_data.get("p_value"),
            details=te_data.get("details", {}),
        )

    def causal_assumptions(self, causal_run: CausalAnalysisRun) -> tuple[str, ...]:
        assumptions: list[str] = []
        id_data = causal_run.result.get("identification", {})
        if id_data.get("required_assumptions"):
            assumptions.extend(id_data["required_assumptions"])
        report = causal_run.result.get("assumption_report", {})
        for check in report.get("checks", []):
            if check.get("status") != "passed":
                assumptions.append(check.get("explanation", check.get("name", "Assumption issue")))
        return tuple(assumptions)
