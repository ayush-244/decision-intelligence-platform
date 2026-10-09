"""Effect size calculations for statistical analyses."""

from __future__ import annotations

import numpy as np
from scipy import stats

from app.application.dto.statistics import EffectSizeDTO
from app.application.services.statistics.data_extractor import ExtractedData
from app.domain.value_objects.statistics import StatisticalTestType


def _magnitude_cohens_d(d: float) -> str:
    ad = abs(d)
    if ad < 0.2:
        return "negligible"
    if ad < 0.5:
        return "small"
    if ad < 0.8:
        return "medium"
    return "large"


def _magnitude_r(r: float) -> str:
    ar = abs(r)
    if ar < 0.1:
        return "negligible"
    if ar < 0.3:
        return "small"
    if ar < 0.5:
        return "medium"
    return "large"


def _magnitude_eta_sq(eta: float) -> str:
    if eta < 0.01:
        return "negligible"
    if eta < 0.06:
        return "small"
    if eta < 0.14:
        return "medium"
    return "large"


def _magnitude_cramers_v(v: float) -> str:
    if v < 0.1:
        return "negligible"
    if v < 0.3:
        return "small"
    if v < 0.5:
        return "medium"
    return "large"


class EffectSizeCalculator:
    """Compute standardized effect sizes with plain-language interpretation."""

    def compute(
        self,
        *,
        test_type: StatisticalTestType,
        extracted: ExtractedData,
        test_statistic: float | None = None,
        p_value: float | None = None,
        details: dict | None = None,
    ) -> tuple[EffectSizeDTO, ...]:
        details = details or {}
        match test_type:
            case StatisticalTestType.INDEPENDENT_TTEST | StatisticalTestType.WELCH_TTEST:
                return self._cohens_d_independent(extracted)
            case StatisticalTestType.PAIRED_TTEST:
                return self._cohens_d_paired(extracted)
            case StatisticalTestType.ONE_SAMPLE_TTEST:
                return self._cohens_d_one_sample(extracted, details)
            case StatisticalTestType.ANOVA:
                return self._eta_squared(details)
            case StatisticalTestType.MANN_WHITNEY_U | StatisticalTestType.WILCOXON_SIGNED_RANK:
                return self._rank_biserial(test_type, extracted, test_statistic)
            case StatisticalTestType.PEARSON_CORRELATION | StatisticalTestType.SPEARMAN_CORRELATION | StatisticalTestType.KENDALL_CORRELATION:
                return self._correlation_effect(details)
            case StatisticalTestType.CHI_SQUARE | StatisticalTestType.FISHER_EXACT:
                return self._cramers_v(details)
            case StatisticalTestType.LOGISTIC_REGRESSION:
                return self._odds_ratios(details)
            case StatisticalTestType.SIMPLE_LINEAR_REGRESSION | StatisticalTestType.MULTIPLE_LINEAR_REGRESSION:
                return self._regression_effect(details)
            case _:
                return ()

    def _cohens_d_independent(self, extracted: ExtractedData) -> tuple[EffectSizeDTO, ...]:
        if extracted.outcome is None or extracted.grouping is None:
            return ()
        groups = np.unique(extracted.grouping)
        if len(groups) != 2:
            return ()
        g1 = extracted.outcome[extracted.grouping == groups[0]].astype(float)
        g2 = extracted.outcome[extracted.grouping == groups[1]].astype(float)
        n1, n2 = len(g1), len(g2)
        if n1 < 2 or n2 < 2:
            return ()
        pooled_std = np.sqrt(((n1 - 1) * g1.var(ddof=1) + (n2 - 1) * g2.var(ddof=1)) / (n1 + n2 - 2))
        if pooled_std == 0:
            return ()
        d = (g1.mean() - g2.mean()) / pooled_std
        df = n1 + n2 - 2
        correction = 1 - (3 / (4 * df - 1)) if df > 1 else 1.0
        g = d * correction
        mag = _magnitude_cohens_d(d)
        return (
            EffectSizeDTO("cohens_d", float(d), f"Mean difference = {d:.3f} standard deviations.", mag),
            EffectSizeDTO("hedges_g", float(g), f"Bias-corrected effect size g = {g:.3f}.", mag),
        )

    def _cohens_d_paired(self, extracted: ExtractedData) -> tuple[EffectSizeDTO, ...]:
        if extracted.outcome is None or extracted.predictor is None:
            return ()
        d_arr = extracted.outcome.astype(float) - extracted.predictor.astype(float)
        if len(d_arr) < 2 or d_arr.std(ddof=1) == 0:
            return ()
        d = d_arr.mean() / d_arr.std(ddof=1)
        mag = _magnitude_cohens_d(d)
        return (EffectSizeDTO("cohens_d", float(d), f"Paired mean difference = {d:.3f} SD.", mag),)

    def _cohens_d_one_sample(self, extracted: ExtractedData, details: dict) -> tuple[EffectSizeDTO, ...]:
        if extracted.outcome is None:
            return ()
        ref = details.get("reference_value", 0.0)
        data = extracted.outcome.astype(float)
        if len(data) < 2 or data.std(ddof=1) == 0:
            return ()
        d = (data.mean() - float(ref)) / data.std(ddof=1)
        mag = _magnitude_cohens_d(d)
        return (EffectSizeDTO("cohens_d", float(d), f"Sample mean differs from {ref} by {d:.3f} SD.", mag),)

    def _eta_squared(self, details: dict) -> tuple[EffectSizeDTO, ...]:
        eta = details.get("eta_squared")
        if eta is None:
            return ()
        mag = _magnitude_eta_sq(float(eta))
        return (
            EffectSizeDTO(
                "eta_squared", float(eta),
                f"{float(eta) * 100:.1f}% of variance in the outcome is explained by group membership.",
                mag,
            ),
        )

    def _rank_biserial(
        self, test_type: StatisticalTestType, extracted: ExtractedData, statistic: float | None
    ) -> tuple[EffectSizeDTO, ...]:
        if statistic is None:
            return ()
        if test_type is StatisticalTestType.MANN_WHITNEY_U and extracted.grouping is not None:
            groups = np.unique(extracted.grouping)
            if len(groups) == 2:
                n1 = int(np.sum(extracted.grouping == groups[0]))
                n2 = int(np.sum(extracted.grouping == groups[1]))
                r = 1 - (2 * statistic) / (n1 * n2)
                return (EffectSizeDTO("rank_biserial", float(r), f"Rank-biserial correlation r = {r:.3f}.", _magnitude_r(r)),)
        return ()

    def _correlation_effect(self, details: dict) -> tuple[EffectSizeDTO, ...]:
        r = details.get("correlation")
        if r is None:
            return ()
        r = float(r)
        r_sq = r ** 2
        return (
            EffectSizeDTO("correlation", r, f"Correlation coefficient r = {r:.3f}.", _magnitude_r(r)),
            EffectSizeDTO("r_squared", r_sq, f"{r_sq * 100:.1f}% shared variance.", _magnitude_r(r)),
        )

    def _cramers_v(self, details: dict) -> tuple[EffectSizeDTO, ...]:
        v = details.get("cramers_v")
        if v is None:
            return ()
        v = float(v)
        return (EffectSizeDTO("cramers_v", v, f"Cramér's V = {v:.3f} — strength of association.", _magnitude_cramers_v(v)),)

    def _odds_ratios(self, details: dict) -> tuple[EffectSizeDTO, ...]:
        ors = details.get("odds_ratios", {})
        results = []
        for name, val in ors.items():
            v = float(val)
            interp = f"Odds of outcome multiply by {v:.2f} per unit increase in {name}."
            mag = "large" if v > 2 or v < 0.5 else ("medium" if v > 1.5 or v < 0.67 else "small")
            results.append(EffectSizeDTO(f"odds_ratio_{name}", v, interp, mag))
        return tuple(results)

    def _regression_effect(self, details: dict) -> tuple[EffectSizeDTO, ...]:
        r_sq = details.get("r_squared")
        if r_sq is None:
            return ()
        r_sq = float(r_sq)
        return (
            EffectSizeDTO(
                "r_squared", r_sq,
                f"Model explains {r_sq * 100:.1f}% of variance in the outcome.",
                _magnitude_eta_sq(r_sq),
            ),
        )
