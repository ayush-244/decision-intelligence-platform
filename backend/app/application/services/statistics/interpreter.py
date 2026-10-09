"""Business interpretation and explainable result generation."""

from __future__ import annotations

from app.application.dto.statistics import (
    AnalysisInterpretationDTO,
    AssumptionReportDTO,
    EffectSizeDTO,
    StatisticalTestResultDTO,
    TestRecommendationDTO,
)
from app.domain.value_objects.statistics import StatisticalTestType


class ResultInterpreter:
    """Translate statistical outputs into decision-ready explanations."""

    def interpret(
        self,
        *,
        recommendation: TestRecommendationDTO,
        assumption_report: AssumptionReportDTO,
        test_result: StatisticalTestResultDTO | None,
        effect_sizes: tuple[EffectSizeDTO, ...],
        research_question: str,
    ) -> AnalysisInterpretationDTO:
        test_name = (
            test_result.test_type.value.replace("_", " ").title()
            if test_result
            else recommendation.recommended_test.value.replace("_", " ").title()
        )

        practical = self._practical_significance(test_result, effect_sizes)
        business = self._business_interpretation(test_result, effect_sizes, research_question)
        limitations = self._limitations(assumption_report, test_result)
        next_steps = self._next_steps(assumption_report, test_result, effect_sizes)

        return AnalysisInterpretationDTO(
            test_performed=test_name,
            selection_reason=recommendation.reasoning,
            practical_significance=practical,
            business_interpretation=business,
            limitations=limitations,
            recommended_next_steps=next_steps,
        )

    def _practical_significance(
        self, test_result: StatisticalTestResultDTO | None, effect_sizes: tuple[EffectSizeDTO, ...]
    ) -> str:
        if not effect_sizes:
            return (
                "Effect size not computed. Statistical significance alone does not indicate "
                "whether a difference is meaningful in practice."
            )
        primary = effect_sizes[0]
        sig_note = ""
        if test_result and test_result.p_value is not None:
            if test_result.is_significant and primary.magnitude in {"negligible", "small"}:
                sig_note = (
                    " The result is statistically significant but the effect is small — "
                    "the practical impact may be limited."
                )
            elif not test_result.is_significant and primary.magnitude in {"medium", "large"}:
                sig_note = (
                    " The effect appears practically meaningful but did not reach statistical "
                    "significance — consider increasing sample size."
                )
        return (
            f"{primary.name}: {primary.value:.4f} ({primary.magnitude} effect). "
            f"{primary.interpretation}{sig_note}"
        )

    def _business_interpretation(
        self,
        test_result: StatisticalTestResultDTO | None,
        effect_sizes: tuple[EffectSizeDTO, ...],
        research_question: str,
    ) -> str:
        if test_result is None:
            return f"Descriptive analysis for: {research_question}"

        if test_result.test_type is StatisticalTestType.DESCRIPTIVE:
            return f"Summary statistics computed to describe the data relevant to: {research_question}"

        p_str = f"p = {test_result.p_value:.4f}" if test_result.p_value is not None else "p unavailable"
        if test_result.is_significant:
            conclusion = (
                f"There is statistically significant evidence (α = {test_result.alpha}, {p_str}) "
                f"relevant to your question: {research_question}"
            )
        else:
            conclusion = (
                f"No statistically significant evidence was found (α = {test_result.alpha}, {p_str}) "
                f"for: {research_question}. This does not prove the absence of an effect."
            )

        if effect_sizes:
            conclusion += f" Effect size ({effect_sizes[0].name} = {effect_sizes[0].value:.3f}) helps assess practical importance."
        return conclusion

    def _limitations(
        self,
        assumption_report: AssumptionReportDTO,
        test_result: StatisticalTestResultDTO | None,
    ) -> tuple[str, ...]:
        limits: list[str] = []
        failed = [c for c in assumption_report.checks if c.status == "failed"]
        warnings = [c for c in assumption_report.checks if c.status == "warning"]
        for check in failed:
            limits.append(f"Assumption violated: {check.name} — {check.explanation}")
        for check in warnings:
            limits.append(f"Caution: {check.name} — {check.explanation}")
        if test_result and test_result.p_value is not None and test_result.is_significant:
            limits.append("Statistical significance does not imply causation.")
        if not limits:
            limits.append("Results assume independent observations and representative sampling.")
        return tuple(limits)

    def _next_steps(
        self,
        assumption_report: AssumptionReportDTO,
        test_result: StatisticalTestResultDTO | None,
        effect_sizes: tuple[EffectSizeDTO, ...],
    ) -> tuple[str, ...]:
        steps: list[str] = []
        if assumption_report.alternatives:
            steps.append(f"Consider alternative methods: {', '.join(assumption_report.alternatives[:3])}.")
        if test_result and not test_result.is_significant:
            steps.append("Increase sample size or refine measurement to improve statistical power.")
        if effect_sizes and effect_sizes[0].magnitude == "negligible":
            steps.append("Evaluate whether the observed difference justifies operational action.")
        if test_result and test_result.test_type in {
            StatisticalTestType.SIMPLE_LINEAR_REGRESSION,
            StatisticalTestType.MULTIPLE_LINEAR_REGRESSION,
        }:
            steps.append("Review residual diagnostics and consider interaction terms or transformations.")
        if not steps:
            steps.append("Document findings and validate with holdout data or a replication study.")
        return tuple(steps)
