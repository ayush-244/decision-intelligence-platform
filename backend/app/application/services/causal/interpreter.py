"""Causal interpretation engine — business-ready explanations."""

from __future__ import annotations

from app.application.dto.causal import (
    AssumptionReportDTO,
    CausalInterpretationDTO,
    IdentificationReportDTO,
    RefutationResultDTO,
    SensitivityResultDTO,
    TreatmentEffectDTO,
)


class CausalInterpreter:
    """Generate transparent, decision-ready causal interpretations."""

    def interpret(
        self,
        *,
        business_question: str,
        treatment: str,
        outcome: str,
        identification: IdentificationReportDTO,
        assumptions: AssumptionReportDTO,
        treatment_effect: TreatmentEffectDTO,
        refutation_results: tuple[RefutationResultDTO, ...],
        sensitivity: SensitivityResultDTO | None,
    ) -> CausalInterpretationDTO:
        causal_valid = identification.identified and assumptions.all_passed
        ate = treatment_effect.ate

        if ate is not None and causal_valid:
            direction = "increases" if ate > 0 else "decreases"
            business = (
                f"Under the stated assumptions and DAG, changing {treatment} causally {direction} "
                f"{outcome} by approximately {abs(ate):.4f} units on average (ATE). "
                f"Question: {business_question}"
            )
            if treatment_effect.ci_lower is not None and treatment_effect.ci_upper is not None:
                business += (
                    f" 95% CI: [{treatment_effect.ci_lower:.4f}, {treatment_effect.ci_upper:.4f}]."
                )
        elif ate is not None:
            business = (
                f"Observed association: {treatment} → {outcome} difference = {ate:.4f}. "
                "This is NOT a validated causal claim — identification or assumptions failed. "
                f"Question: {business_question}"
            )
        else:
            business = f"Could not estimate treatment effect for: {business_question}"

        limitations = list(identification.limitations)
        for check in assumptions.checks:
            if check.status in {"failed", "warning"}:
                limitations.append(f"{check.name}: {check.explanation}")
        if refutation_results:
            failed = [r for r in refutation_results if not r.passed]
            if failed:
                limitations.append(
                    f"{len(failed)} refutation test(s) failed — estimate may not be robust."
                )
        if sensitivity and sensitivity.violations:
            limitations.extend(sensitivity.violations)

        limitations.append("Correlation alone does not imply causation.")
        limitations.append("Unmeasured confounders can invalidate any observational estimate.")

        next_steps: list[str] = []
        if not identification.identified:
            next_steps.append("Revise the DAG or collect data on additional confounders.")
        if not assumptions.all_passed:
            next_steps.append("Address failed assumptions before acting on results.")
        if sensitivity and sensitivity.robustness_score < 0.6:
            next_steps.append("Run A/B test or quasi-experiment to validate observational finding.")
        if treatment_effect.att is not None and treatment_effect.atc is not None:
            next_steps.append(
                f"Compare ATT ({treatment_effect.att:.4f}) vs ATC ({treatment_effect.atc:.4f}) "
                "for heterogeneous effects."
            )
        if not next_steps:
            next_steps.append("Document assumptions and replicate on holdout data.")

        return CausalInterpretationDTO(
            objective=business_question,
            business_interpretation=business,
            limitations=tuple(dict.fromkeys(limitations)),
            recommended_next_steps=tuple(next_steps),
            causal_claim_valid=causal_valid and (sensitivity.robustness_score >= 0.5 if sensitivity else False),
        )
