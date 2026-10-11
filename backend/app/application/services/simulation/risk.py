"""Risk assessment for simulated interventions."""

from __future__ import annotations

from typing import Any

from app.application.dto.simulation import (
    ConstraintEvaluationDTO,
    CounterfactualOutcomeDTO,
    RiskAssessmentDTO,
    RiskContributorDTO,
)
from app.domain.entities.causal_analysis import CausalAnalysisRun


class RiskEngine:
    """Aggregate statistical, model, and operational risk for interventions."""

    def assess(
        self,
        *,
        counterfactual: CounterfactualOutcomeDTO,
        causal_run: CausalAnalysisRun,
        constraint_evaluations: tuple[ConstraintEvaluationDTO, ...],
    ) -> RiskAssessmentDTO:
        sensitivity = causal_run.result.get("sensitivity") or {}
        robustness = float(sensitivity.get("robustness_score", 0.5))
        identified = bool(causal_run.result.get("identification", {}).get("identified", False))

        statistical = min(1.0, counterfactual.uncertainty_score)
        sensitivity_risk = 1.0 - robustness
        model_confidence = 0.8 if identified else 0.4
        hidden_confounding = max(0.0, 1.0 - robustness) * 0.7
        extrapolation = min(1.0, len(counterfactual.extrapolation_warnings) * 0.25)
        implementation = min(1.0, extrapolation + statistical * 0.3)

        hard_violations = sum(
            1 for c in constraint_evaluations
            if not c.satisfied and c.constraint.severity == "hard"
        )
        operational = min(1.0, hard_violations * 0.35 + statistical * 0.2)

        contributors = (
            RiskContributorDTO(
                "Statistical uncertainty",
                round(statistical, 3),
                0.25,
                "Width of causal estimate and counterfactual confidence interval.",
            ),
            RiskContributorDTO(
                "Model confidence",
                round(1.0 - model_confidence, 3),
                0.20,
                "Based on causal identification success and refutation robustness.",
            ),
            RiskContributorDTO(
                "Hidden confounding",
                round(hidden_confounding, 3),
                0.20,
                "Sensitivity to unmeasured confounders from Phase 6 analysis.",
            ),
            RiskContributorDTO(
                "Extrapolation",
                round(extrapolation, 3),
                0.15,
                "Intervention extends beyond observed data support.",
            ),
            RiskContributorDTO(
                "Operational",
                round(operational, 3),
                0.20,
                "Constraint violations and implementation complexity.",
            ),
        )
        overall = sum(c.score * c.weight for c in contributors) / sum(c.weight for c in contributors)
        summary = self._summary(overall, contributors)

        return RiskAssessmentDTO(
            overall_score=round(overall, 3),
            implementation_risk=round(implementation, 3),
            statistical_uncertainty=round(statistical, 3),
            sensitivity_risk=round(sensitivity_risk, 3),
            model_confidence=round(model_confidence, 3),
            hidden_confounding_risk=round(hidden_confounding, 3),
            operational_risk=round(operational, 3),
            contributors=contributors,
            summary=summary,
        )

    @staticmethod
    def assess_from_payload(
        *,
        counterfactual_data: dict[str, Any],
        causal_result: dict[str, Any],
        constraints: list[dict[str, Any]] | None = None,
    ) -> RiskAssessmentDTO:
        from app.application.dto.simulation import ConstraintDTO, CounterfactualOutcomeDTO

        cf = CounterfactualOutcomeDTO(
            baseline_outcome=counterfactual_data.get("baseline_outcome", 0),
            expected_outcome=counterfactual_data.get("expected_outcome", 0),
            expected_treatment_effect=counterfactual_data.get("expected_treatment_effect", 0),
            ci_lower=counterfactual_data.get("ci_lower", 0),
            ci_upper=counterfactual_data.get("ci_upper", 0),
            probability_improvement=counterfactual_data.get("probability_improvement", 0.5),
            probability_deterioration=counterfactual_data.get("probability_deterioration", 0.5),
            uncertainty_score=counterfactual_data.get("uncertainty_score", 0.5),
            extrapolation_warnings=tuple(counterfactual_data.get("extrapolation_warnings", [])),
        )

        class _StubRun:
            result = causal_result

        evals: tuple[ConstraintEvaluationDTO, ...] = ()
        if constraints:
            from app.application.dto.simulation import ROIEstimateDTO
            from app.application.services.simulation.constraints import ConstraintEngine

            roi_stub = ROIEstimateDTO(0, 0, 0, 0, None, 0, ())
            evals = ConstraintEngine().evaluate(
                constraints=tuple(
                    ConstraintDTO(
                        type=c.get("type", "custom"),
                        severity=c.get("severity", "soft"),
                        threshold=c.get("threshold"),
                        description=c.get("description", ""),
                    )
                    for c in constraints
                ),
                counterfactual=cf,
                roi=roi_stub,
            )

        engine = RiskEngine()
        return engine.assess(
            counterfactual=cf,
            causal_run=_StubRun(),  # type: ignore[arg-type]
            constraint_evaluations=evals,
        )

    @staticmethod
    def _summary(overall: float, contributors: tuple[RiskContributorDTO, ...]) -> str:
        level = "low" if overall < 0.35 else "moderate" if overall < 0.65 else "high"
        top = max(contributors, key=lambda c: c.score * c.weight)
        return (
            f"Overall {level} risk ({overall:.0%}). Primary driver: {top.name} — {top.explanation}"
        )
