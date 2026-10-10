"""Sensitivity analysis for hidden confounding."""

from __future__ import annotations

from app.application.dto.causal import RefutationResultDTO, SensitivityResultDTO, TreatmentEffectDTO


class SensitivityEngine:
    """Assess robustness to unmeasured confounding."""

    def analyze(
        self,
        *,
        treatment_effect: TreatmentEffectDTO,
        refutation_results: tuple[RefutationResultDTO, ...],
        identified: bool,
    ) -> SensitivityResultDTO:
        violations: list[str] = []
        refutation_pass_rate = 0.0
        if refutation_results:
            refutation_pass_rate = sum(1 for r in refutation_results if r.passed) / len(refutation_results)

        if not identified:
            violations.append("Causal effect not identified from DAG.")
        if treatment_effect.ate is not None and treatment_effect.std_error:
            signal = abs(treatment_effect.ate) / treatment_effect.std_error
            if signal < 1.96:
                violations.append("Effect not statistically significant at 95% level.")
        if refutation_pass_rate < 0.5:
            violations.append("Majority of refutation tests failed.")

        # Rosenbaum-style gamma approximation: how much confounding would flip the conclusion
        gamma = None
        if treatment_effect.ate and treatment_effect.std_error and treatment_effect.std_error > 0:
            gamma = 1.0 + abs(treatment_effect.ate) / (2 * treatment_effect.std_error)

        robustness = min(1.0, refutation_pass_rate * (1.0 if identified else 0.3))

        explanation = (
            f"Robustness score: {robustness:.0%}. "
            f"{sum(1 for r in refutation_results if r.passed)}/{len(refutation_results) or 1} refutation tests passed. "
        )
        if gamma:
            explanation += (
                f"Approximate sensitivity parameter Γ ≈ {gamma:.2f} — "
                "an unmeasured confounder would need to change odds of treatment by this factor "
                "to explain away the effect (simplified bound)."
            )
        else:
            explanation += "Insufficient data for gamma sensitivity bound."

        return SensitivityResultDTO(
            robustness_score=robustness,
            gamma_threshold=gamma,
            explanation=explanation,
            violations=tuple(violations),
        )
