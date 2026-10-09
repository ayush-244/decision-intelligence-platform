"""Confidence interval calculations."""

from __future__ import annotations

import numpy as np
from scipy import stats

from app.application.dto.statistics import ConfidenceIntervalDTO
from app.application.services.statistics.data_extractor import ExtractedData
from app.domain.value_objects.statistics import StatisticalTestType


class ConfidenceIntervalEngine:
    """Compute confidence intervals with plain-language interpretation."""

    def compute(
        self,
        *,
        test_type: StatisticalTestType,
        extracted: ExtractedData,
        confidence_level: float,
        details: dict | None = None,
    ) -> tuple[ConfidenceIntervalDTO, ...]:
        details = details or {}
        alpha = 1 - confidence_level
        intervals: list[ConfidenceIntervalDTO] = []

        if test_type in {
            StatisticalTestType.INDEPENDENT_TTEST,
            StatisticalTestType.WELCH_TTEST,
            StatisticalTestType.ONE_SAMPLE_TTEST,
            StatisticalTestType.PAIRED_TTEST,
        }:
            ci = self._mean_difference_ci(test_type, extracted, confidence_level, details)
            if ci:
                intervals.append(ci)

        if test_type in {
            StatisticalTestType.PEARSON_CORRELATION,
            StatisticalTestType.SPEARMAN_CORRELATION,
        }:
            ci = self._correlation_ci(details, confidence_level)
            if ci:
                intervals.append(ci)

        if test_type is StatisticalTestType.DESCRIPTIVE and extracted.outcome is not None:
            ci = self._mean_ci(extracted.outcome.astype(float), confidence_level, "outcome_mean")
            if ci:
                intervals.append(ci)

        for coef in details.get("coefficient_cis", []):
            intervals.append(
                ConfidenceIntervalDTO(
                    parameter=coef["name"],
                    lower=float(coef["lower"]),
                    upper=float(coef["upper"]),
                    level=confidence_level,
                    interpretation=(
                        f"We are {confidence_level * 100:.0f}% confident the true {coef['name']} "
                        f"lies between {coef['lower']:.4f} and {coef['upper']:.4f}."
                    ),
                )
            )

        return tuple(intervals)

    def _mean_difference_ci(
        self,
        test_type: StatisticalTestType,
        extracted: ExtractedData,
        level: float,
        details: dict,
    ) -> ConfidenceIntervalDTO | None:
        if test_type is StatisticalTestType.PAIRED_TTEST:
            if extracted.outcome is None or extracted.predictor is None:
                return None
            diffs = extracted.outcome.astype(float) - extracted.predictor.astype(float)
            return self._mean_ci(diffs, level, "mean_difference")

        if test_type is StatisticalTestType.ONE_SAMPLE_TTEST:
            if extracted.outcome is None:
                return None
            data = extracted.outcome.astype(float)
            ref = float(details.get("reference_value", 0.0))
            ci = self._mean_ci(data, level, "population_mean")
            if ci:
                return ConfidenceIntervalDTO(
                    parameter="mean_vs_reference",
                    lower=ci.lower - ref,
                    upper=ci.upper - ref,
                    level=level,
                    interpretation=(
                        f"We are {level * 100:.0f}% confident the true mean differs from the reference "
                        f"by between {ci.lower - ref:.4f} and {ci.upper - ref:.4f}."
                    ),
                )
            return None

        if extracted.outcome is None or extracted.grouping is None:
            return None
        groups = np.unique(extracted.grouping)
        if len(groups) != 2:
            return None
        g1 = extracted.outcome[extracted.grouping == groups[0]].astype(float)
        g2 = extracted.outcome[extracted.grouping == groups[1]].astype(float)
        diff = g1.mean() - g2.mean()
        se = np.sqrt(g1.var(ddof=1) / len(g1) + g2.var(ddof=1) / len(g2))
        df = len(g1) + len(g2) - 2
        t_crit = stats.t.ppf(1 - (1 - level) / 2, df)
        margin = t_crit * se
        return ConfidenceIntervalDTO(
            parameter="mean_difference",
            lower=float(diff - margin),
            upper=float(diff + margin),
            level=level,
            interpretation=(
                f"We are {level * 100:.0f}% confident the true difference in group means "
                f"lies between {diff - margin:.4f} and {diff + margin:.4f}."
            ),
        )

    def _mean_ci(self, data: np.ndarray, level: float, parameter: str) -> ConfidenceIntervalDTO | None:
        n = len(data)
        if n < 2:
            return None
        mean = float(data.mean())
        se = float(stats.sem(data))
        t_crit = float(stats.t.ppf(1 - (1 - level) / 2, n - 1))
        margin = t_crit * se
        return ConfidenceIntervalDTO(
            parameter=parameter,
            lower=mean - margin,
            upper=mean + margin,
            level=level,
            interpretation=(
                f"We are {level * 100:.0f}% confident the true mean lies between "
                f"{mean - margin:.4f} and {mean + margin:.4f}."
            ),
        )

    def _correlation_ci(self, details: dict, level: float) -> ConfidenceIntervalDTO | None:
        r = details.get("correlation")
        n = details.get("n")
        if r is None or n is None or n < 4:
            return None
        r = float(r)
        n = int(n)
        z = np.arctanh(r)
        se = 1 / np.sqrt(n - 3)
        z_crit = stats.norm.ppf(1 - (1 - level) / 2)
        lo = np.tanh(z - z_crit * se)
        hi = np.tanh(z + z_crit * se)
        return ConfidenceIntervalDTO(
            parameter="correlation",
            lower=float(lo),
            upper=float(hi),
            level=level,
            interpretation=(
                f"We are {level * 100:.0f}% confident the true correlation lies between {lo:.4f} and {hi:.4f}."
            ),
        )
