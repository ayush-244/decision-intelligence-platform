"""Assumption validation engine for statistical analyses."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy import stats

from app.application.dto.statistics import AssumptionCheckDTO, AssumptionReportDTO
from app.application.services.statistics.data_extractor import AnalysisDataExtractor, ExtractedData, is_numeric
from app.domain.value_objects.statistics import AssumptionStatus, StatisticalTestType


class AssumptionValidator:
    """Validate statistical assumptions and recommend alternatives when violated."""

    def __init__(self) -> None:
        self._extractor = AnalysisDataExtractor()

    def validate(
        self,
        *,
        test_type: StatisticalTestType,
        frame: pl.DataFrame,
        extracted: ExtractedData,
        alpha: float = 0.05,
    ) -> AssumptionReportDTO:
        checks: list[AssumptionCheckDTO] = []
        alternatives: list[str] = []

        if test_type in {
            StatisticalTestType.INDEPENDENT_TTEST,
            StatisticalTestType.WELCH_TTEST,
            StatisticalTestType.PAIRED_TTEST,
            StatisticalTestType.ONE_SAMPLE_TTEST,
            StatisticalTestType.ANOVA,
        }:
            checks.extend(self._normality_checks(test_type, extracted, alpha))
            if test_type in {StatisticalTestType.INDEPENDENT_TTEST, StatisticalTestType.ANOVA}:
                checks.append(self._equal_variance_check(extracted, alpha))

        if test_type in {StatisticalTestType.PEARSON_CORRELATION, StatisticalTestType.SIMPLE_LINEAR_REGRESSION}:
            checks.append(self._linearity_check(extracted))
            if extracted.outcome is not None:
                checks.append(self._normality_single(extracted.outcome, "Outcome normality", alpha))

        if test_type is StatisticalTestType.MULTIPLE_LINEAR_REGRESSION:
            checks.append(self._multicollinearity_check(frame, extracted))
            checks.append(self._linearity_check(extracted))

        if test_type in {StatisticalTestType.CHI_SQUARE, StatisticalTestType.FISHER_EXACT}:
            checks.append(self._expected_frequencies_check(frame, extracted))

        checks.append(self._sample_size_check(test_type, extracted))
        checks.append(self._missing_data_check(frame, extracted))
        checks.append(self._independence_check())

        failed = [c for c in checks if c.status == AssumptionStatus.FAILED.value]
        warnings = [c for c in checks if c.status == AssumptionStatus.WARNING.value]

        if failed or warnings:
            alternatives.extend(self._suggest_alternatives(test_type, checks))

        all_passed = not failed
        return AssumptionReportDTO(
            checks=tuple(checks),
            all_passed=all_passed,
            alternatives=tuple(dict.fromkeys(alternatives)),
        )

    def _normality_checks(
        self, test_type: StatisticalTestType, extracted: ExtractedData, alpha: float
    ) -> list[AssumptionCheckDTO]:
        checks: list[AssumptionCheckDTO] = []
        if test_type is StatisticalTestType.PAIRED_TTEST:
            if extracted.outcome is not None and extracted.predictor is not None:
                diffs = extracted.outcome[: min(len(extracted.outcome), len(extracted.predictor))].astype(float)
                if len(extracted.predictor) == len(extracted.outcome):
                    diffs = extracted.outcome.astype(float) - extracted.predictor.astype(float)
                checks.append(self._shapiro("Normality of differences", diffs, alpha))
            return checks

        if test_type is StatisticalTestType.ONE_SAMPLE_TTEST and extracted.outcome is not None:
            checks.append(self._shapiro("Normality", extracted.outcome.astype(float), alpha))
            return checks

        if extracted.outcome is not None and extracted.grouping is not None:
            for group_val in np.unique(extracted.grouping):
                mask = extracted.grouping == group_val
                group_data = extracted.outcome[mask].astype(float)
                if len(group_data) >= 3:
                    checks.append(self._shapiro(f"Normality (group {group_val})", group_data, alpha))
        return checks

    def _shapiro(self, name: str, data: np.ndarray, alpha: float) -> AssumptionCheckDTO:
        if len(data) < 3:
            return AssumptionCheckDTO(
                name=name, status=AssumptionStatus.WARNING.value, statistic=None, p_value=None,
                explanation="Sample too small for normality test (n < 3).",
                recommendation="Interpret results cautiously or use non-parametric alternatives.",
            )
        sample = data if len(data) <= 5000 else np.random.default_rng(42).choice(data, 5000, replace=False)
        stat, p = stats.shapiro(sample)
        passed = p >= alpha
        return AssumptionCheckDTO(
            name=name,
            status=AssumptionStatus.PASSED.value if passed else AssumptionStatus.FAILED.value,
            statistic=float(stat),
            p_value=float(p),
            explanation=(
                f"Shapiro-Wilk test: data {'appears' if passed else 'does not appear'} normally distributed (p={p:.4f})."
            ),
            recommendation=None if passed else "Consider Mann-Whitney U or Wilcoxon signed-rank test.",
        )

    def _normality_single(self, data: np.ndarray, name: str, alpha: float) -> AssumptionCheckDTO:
        return self._shapiro(name, data.astype(float), alpha)

    def _equal_variance_check(self, extracted: ExtractedData, alpha: float) -> AssumptionCheckDTO:
        if extracted.outcome is None or extracted.grouping is None:
            return AssumptionCheckDTO(
                name="Equal variances", status=AssumptionStatus.NOT_APPLICABLE.value,
                statistic=None, p_value=None, explanation="Grouping variable not provided.",
            )
        groups = []
        for gv in np.unique(extracted.grouping):
            groups.append(extracted.outcome[extracted.grouping == gv].astype(float))
        if len(groups) < 2:
            return AssumptionCheckDTO(
                name="Equal variances", status=AssumptionStatus.NOT_APPLICABLE.value,
                statistic=None, p_value=None, explanation="Need at least two groups.",
            )
        stat, p = stats.levene(*groups)
        passed = p >= alpha
        return AssumptionCheckDTO(
            name="Equal variances",
            status=AssumptionStatus.PASSED.value if passed else AssumptionStatus.FAILED.value,
            statistic=float(stat), p_value=float(p),
            explanation=f"Levene's test: variances {'appear' if passed else 'do not appear'} equal (p={p:.4f}).",
            recommendation=None if passed else "Use Welch's t-test which does not assume equal variances.",
        )

    def _linearity_check(self, extracted: ExtractedData) -> AssumptionCheckDTO:
        if extracted.outcome is None or extracted.predictor is None:
            return AssumptionCheckDTO(
                name="Linearity", status=AssumptionStatus.NOT_APPLICABLE.value,
                statistic=None, p_value=None, explanation="Requires numeric outcome and predictor.",
            )
        try:
            x = extracted.predictor.astype(float)
            y = extracted.outcome.astype(float)
            n = min(len(x), len(y))
            r, _ = stats.pearsonr(x[:n], y[:n])
            strength = abs(r)
            if strength >= 0.3:
                status = AssumptionStatus.PASSED.value
                explanation = f"Pearson r={r:.3f} suggests a linear relationship."
            elif strength >= 0.1:
                status = AssumptionStatus.WARNING.value
                explanation = f"Weak linear relationship (r={r:.3f}). Consider transformations."
            else:
                status = AssumptionStatus.WARNING.value
                explanation = f"Very weak linear relationship (r={r:.3f}). Linear model may be inappropriate."
            return AssumptionCheckDTO(
                name="Linearity", status=status, statistic=float(r), p_value=None,
                explanation=explanation,
            )
        except (ValueError, TypeError):
            return AssumptionCheckDTO(
                name="Linearity", status=AssumptionStatus.WARNING.value,
                statistic=None, p_value=None, explanation="Could not assess linearity — non-numeric data.",
            )

    def _multicollinearity_check(self, frame: pl.DataFrame, extracted: ExtractedData) -> AssumptionCheckDTO:
        predictors = list(extracted.covariates.keys())
        if extracted.predictor_name:
            predictors.insert(0, extracted.predictor_name)
        if len(predictors) < 2:
            return AssumptionCheckDTO(
                name="Multicollinearity", status=AssumptionStatus.NOT_APPLICABLE.value,
                statistic=None, p_value=None, explanation="Single predictor — VIF not applicable.",
            )
        cols = [c for c in predictors if c in frame.columns and is_numeric(frame[c].dtype)]
        if len(cols) < 2:
            return AssumptionCheckDTO(
                name="Multicollinearity", status=AssumptionStatus.NOT_APPLICABLE.value,
                statistic=None, p_value=None, explanation="Insufficient numeric predictors.",
            )
        matrix = frame.select(cols).drop_nulls().to_numpy()
        if matrix.shape[0] < len(cols) + 1:
            return AssumptionCheckDTO(
                name="Multicollinearity", status=AssumptionStatus.WARNING.value,
                statistic=None, p_value=None, explanation="Too few observations for VIF assessment.",
            )
        corr = np.corrcoef(matrix, rowvar=False)
        max_corr = float(np.max(np.abs(corr - np.eye(len(cols)))))
        if max_corr > 0.9:
            return AssumptionCheckDTO(
                name="Multicollinearity", status=AssumptionStatus.FAILED.value,
                statistic=max_corr, p_value=None,
                explanation=f"High inter-predictor correlation (max |r|={max_corr:.3f}). VIF likely elevated.",
                recommendation="Remove or combine highly correlated predictors.",
            )
        return AssumptionCheckDTO(
            name="Multicollinearity", status=AssumptionStatus.PASSED.value,
            statistic=max_corr, p_value=None,
            explanation=f"Maximum inter-predictor correlation |r|={max_corr:.3f} — acceptable.",
        )

    def _expected_frequencies_check(self, frame: pl.DataFrame, extracted: ExtractedData) -> AssumptionCheckDTO:
        if extracted.predictor_name is None or extracted.outcome_name is None:
            return AssumptionCheckDTO(
                name="Expected frequencies", status=AssumptionStatus.NOT_APPLICABLE.value,
                statistic=None, p_value=None, explanation="Requires two categorical variables.",
            )
        ct = frame.group_by([extracted.outcome_name, extracted.predictor_name]).len()
        counts = ct["len"].to_numpy()
        if len(counts) == 0:
            return AssumptionCheckDTO(
                name="Expected frequencies", status=AssumptionStatus.FAILED.value,
                statistic=0.0, p_value=None, explanation="Contingency table is empty.",
                recommendation="Use Fisher's exact test for small samples.",
            )
        min_expected = float(np.min(counts))
        passed = min_expected >= 5
        return AssumptionCheckDTO(
            name="Expected frequencies",
            status=AssumptionStatus.PASSED.value if passed else AssumptionStatus.FAILED.value,
            statistic=min_expected, p_value=None,
            explanation=f"Minimum cell count = {min_expected:.0f}. Chi-square requires expected counts ≥ 5.",
            recommendation=None if passed else "Use Fisher's exact test instead of chi-square.",
        )

    def _sample_size_check(self, test_type: StatisticalTestType, extracted: ExtractedData) -> AssumptionCheckDTO:
        n = 0
        if extracted.outcome is not None:
            n = len(extracted.outcome)
        min_required = 2 if test_type is StatisticalTestType.DESCRIPTIVE else 5
        passed = n >= min_required
        return AssumptionCheckDTO(
            name="Sample size",
            status=AssumptionStatus.PASSED.value if passed else AssumptionStatus.FAILED.value,
            statistic=float(n), p_value=None,
            explanation=f"n={n}. Minimum recommended n={min_required} for {test_type.value}.",
            recommendation=None if passed else "Collect more data before drawing conclusions.",
        )

    def _missing_data_check(self, frame: pl.DataFrame, extracted: ExtractedData) -> AssumptionCheckDTO:
        cols = [c for c in [extracted.outcome_name, extracted.predictor_name, extracted.grouping_name] if c]
        cols.extend(extracted.covariates.keys())
        if not cols:
            return AssumptionCheckDTO(
                name="Missing data", status=AssumptionStatus.NOT_APPLICABLE.value,
                statistic=None, p_value=None, explanation="No variables specified.",
            )
        total = frame.height
        missing = sum(frame[c].null_count() for c in cols if c in frame.columns)
        pct = (missing / (total * len(cols))) * 100 if total > 0 else 0.0
        status = AssumptionStatus.PASSED.value if pct < 10 else AssumptionStatus.WARNING.value
        return AssumptionCheckDTO(
            name="Missing data", status=status, statistic=pct, p_value=None,
            explanation=f"Missing values account for {pct:.1f}% of analysis cells.",
            recommendation="Review missingness patterns if >10%." if pct >= 10 else None,
        )

    def _independence_check(self) -> AssumptionCheckDTO:
        return AssumptionCheckDTO(
            name="Independence",
            status=AssumptionStatus.NOT_CHECKED.value,
            statistic=None, p_value=None,
            explanation="Independence cannot be verified from data alone — assumed based on study design.",
            recommendation="Confirm observations are independent (no repeated measures unless paired).",
        )

    @staticmethod
    def _suggest_alternatives(test_type: StatisticalTestType, checks: list[AssumptionCheckDTO]) -> list[str]:
        alts: list[str] = []
        failed_names = {c.name.lower() for c in checks if c.status == AssumptionStatus.FAILED.value}
        if test_type is StatisticalTestType.INDEPENDENT_TTEST:
            if any("normality" in n for n in failed_names):
                alts.append(StatisticalTestType.MANN_WHITNEY_U.value)
            if any("variance" in n for n in failed_names):
                alts.append(StatisticalTestType.WELCH_TTEST.value)
        elif test_type is StatisticalTestType.PAIRED_TTEST:
            if any("normality" in n for n in failed_names):
                alts.append(StatisticalTestType.WILCOXON_SIGNED_RANK.value)
        elif test_type is StatisticalTestType.ANOVA:
            if any("normality" in n for n in failed_names):
                alts.append("kruskal_wallis")
        elif test_type is StatisticalTestType.CHI_SQUARE:
            if any("frequenc" in n for n in failed_names):
                alts.append(StatisticalTestType.FISHER_EXACT.value)
        elif test_type is StatisticalTestType.PEARSON_CORRELATION:
            if any("normality" in n or "linear" in n for n in failed_names):
                alts.append(StatisticalTestType.SPEARMAN_CORRELATION.value)
        for c in checks:
            if c.recommendation:
                alts.append(c.recommendation)
        return alts
