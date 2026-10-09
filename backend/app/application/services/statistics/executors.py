"""Statistical test execution engine."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.contingency_tables import mcnemar  # noqa: F401 — reserved

from app.application.dto.statistics import StatisticalTestResultDTO
from app.application.services.statistics.data_extractor import ExtractedData, is_numeric
from app.domain.value_objects.statistics import StatisticalTestType
from app.shared.exceptions import BusinessValidationError


class StatisticalExecutor:
    """Execute statistical tests using scipy and statsmodels."""

    def execute(
        self,
        *,
        test_type: StatisticalTestType,
        frame: pl.DataFrame,
        extracted: ExtractedData,
        alpha: float = 0.05,
        reference_value: float | None = None,
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        handlers = {
            StatisticalTestType.DESCRIPTIVE: self._descriptive,
            StatisticalTestType.ONE_SAMPLE_TTEST: self._one_sample_ttest,
            StatisticalTestType.INDEPENDENT_TTEST: self._independent_ttest,
            StatisticalTestType.WELCH_TTEST: self._welch_ttest,
            StatisticalTestType.PAIRED_TTEST: self._paired_ttest,
            StatisticalTestType.ANOVA: self._anova,
            StatisticalTestType.CHI_SQUARE: self._chi_square,
            StatisticalTestType.FISHER_EXACT: self._fisher_exact,
            StatisticalTestType.MANN_WHITNEY_U: self._mann_whitney,
            StatisticalTestType.WILCOXON_SIGNED_RANK: self._wilcoxon,
            StatisticalTestType.PEARSON_CORRELATION: self._pearson,
            StatisticalTestType.SPEARMAN_CORRELATION: self._spearman,
            StatisticalTestType.KENDALL_CORRELATION: self._kendall,
            StatisticalTestType.SIMPLE_LINEAR_REGRESSION: self._simple_regression,
            StatisticalTestType.MULTIPLE_LINEAR_REGRESSION: self._multiple_regression,
            StatisticalTestType.LOGISTIC_REGRESSION: self._logistic_regression,
        }
        handler = handlers.get(test_type)
        if handler is None:
            raise BusinessValidationError(f"Unsupported test type: {test_type.value}")
        return handler(frame, extracted, alpha, reference_value)

    def _descriptive(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        return (
            StatisticalTestResultDTO(
                test_type=StatisticalTestType.DESCRIPTIVE,
                statistic=None, p_value=None, degrees_of_freedom=None,
                is_significant=False, alpha=alpha, details={"note": "Descriptive analysis — no hypothesis test."},
            ),
            {},
        )

    def _one_sample_ttest(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        if extracted.outcome is None:
            raise BusinessValidationError("Outcome variable required for one-sample t-test.")
        popmean = ref if ref is not None else 0.0
        data = extracted.outcome.astype(float)
        stat, p = stats.ttest_1samp(data, popmean)
        return self._ttest_result(StatisticalTestType.ONE_SAMPLE_TTEST, stat, p, len(data) - 1, alpha, {"reference_value": popmean})

    def _independent_ttest(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        g1, g2 = self._two_groups(extracted)
        stat, p = stats.ttest_ind(g1, g2, equal_var=True)
        return self._ttest_result(StatisticalTestType.INDEPENDENT_TTEST, stat, p, len(g1) + len(g2) - 2, alpha, {})

    def _welch_ttest(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        g1, g2 = self._two_groups(extracted)
        stat, p = stats.ttest_ind(g1, g2, equal_var=False)
        return self._ttest_result(StatisticalTestType.WELCH_TTEST, stat, p, None, alpha, {})

    def _paired_ttest(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        if extracted.outcome is None or extracted.predictor is None:
            raise BusinessValidationError("Paired t-test requires outcome and predictor variables.")
        a = extracted.outcome.astype(float)
        b = extracted.predictor.astype(float)
        n = min(len(a), len(b))
        stat, p = stats.ttest_rel(a[:n], b[:n])
        return self._ttest_result(StatisticalTestType.PAIRED_TTEST, stat, p, n - 1, alpha, {})

    def _anova(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        if extracted.outcome is None or extracted.grouping is None:
            raise BusinessValidationError("ANOVA requires outcome and grouping variables.")
        groups = []
        for gv in np.unique(extracted.grouping):
            groups.append(extracted.outcome[extracted.grouping == gv].astype(float))
        stat, p = stats.f_oneway(*groups)
        total = np.concatenate(groups)
        ss_between = sum(len(g) * (g.mean() - total.mean()) ** 2 for g in groups)
        ss_total = sum((total - total.mean()) ** 2)
        eta_sq = float(ss_between / ss_total) if ss_total > 0 else 0.0
        return (
            StatisticalTestResultDTO(
                test_type=StatisticalTestType.ANOVA,
                statistic=float(stat), p_value=float(p),
                degrees_of_freedom=float(len(groups) - 1),
                is_significant=p < alpha, alpha=alpha,
                details={"group_count": len(groups), "eta_squared": eta_sq},
            ),
            {"eta_squared": eta_sq},
        )

    def _chi_square(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        table, cramers = self._contingency_table(frame, extracted)
        stat, p, dof, _ = stats.chi2_contingency(table)
        return (
            StatisticalTestResultDTO(
                test_type=StatisticalTestType.CHI_SQUARE,
                statistic=float(stat), p_value=float(p), degrees_of_freedom=float(dof),
                is_significant=p < alpha, alpha=alpha,
                details={"cramers_v": cramers},
            ),
            {"cramers_v": cramers},
        )

    def _fisher_exact(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        table, cramers = self._contingency_table(frame, extracted)
        if table.shape != (2, 2):
            raise BusinessValidationError("Fisher's exact test requires a 2×2 contingency table.")
        odds_ratio, p = stats.fisher_exact(table)
        return (
            StatisticalTestResultDTO(
                test_type=StatisticalTestType.FISHER_EXACT,
                statistic=float(odds_ratio), p_value=float(p), degrees_of_freedom=None,
                is_significant=p < alpha, alpha=alpha,
                details={"odds_ratio": float(odds_ratio), "cramers_v": cramers},
            ),
            {"cramers_v": cramers, "odds_ratio": float(odds_ratio)},
        )

    def _mann_whitney(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        g1, g2 = self._two_groups(extracted)
        stat, p = stats.mannwhitneyu(g1, g2, alternative="two-sided")
        return (
            StatisticalTestResultDTO(
                test_type=StatisticalTestType.MANN_WHITNEY_U,
                statistic=float(stat), p_value=float(p), degrees_of_freedom=None,
                is_significant=p < alpha, alpha=alpha, details={},
            ),
            {},
        )

    def _wilcoxon(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        if extracted.outcome is None or extracted.predictor is None:
            raise BusinessValidationError("Wilcoxon test requires paired outcome and predictor.")
        a = extracted.outcome.astype(float)
        b = extracted.predictor.astype(float)
        n = min(len(a), len(b))
        stat, p = stats.wilcoxon(a[:n], b[:n])
        return (
            StatisticalTestResultDTO(
                test_type=StatisticalTestType.WILCOXON_SIGNED_RANK,
                statistic=float(stat), p_value=float(p), degrees_of_freedom=None,
                is_significant=p < alpha, alpha=alpha, details={},
            ),
            {},
        )

    def _pearson(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        x, y = self._pair_numeric(extracted)
        r, p = stats.pearsonr(x, y)
        return self._correlation_result(StatisticalTestType.PEARSON_CORRELATION, r, p, len(x), alpha)

    def _spearman(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        x, y = self._pair_numeric(extracted)
        r, p = stats.spearmanr(x, y)
        return self._correlation_result(StatisticalTestType.SPEARMAN_CORRELATION, r, p, len(x), alpha)

    def _kendall(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        x, y = self._pair_numeric(extracted)
        r, p = stats.kendalltau(x, y)
        return self._correlation_result(StatisticalTestType.KENDALL_CORRELATION, r, p, len(x), alpha)

    def _simple_regression(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        x, y = self._pair_numeric(extracted)
        x_const = sm.add_constant(x)
        model = sm.OLS(y, x_const).fit()
        return self._regression_result(StatisticalTestType.SIMPLE_LINEAR_REGRESSION, model, alpha)

    def _multiple_regression(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        if extracted.outcome_name is None:
            raise BusinessValidationError("Outcome required for multiple regression.")
        predictors = []
        names = []
        if extracted.predictor_name:
            predictors.append(frame[extracted.predictor_name].cast(pl.Float64).to_numpy())
            names.append(extracted.predictor_name)
        for name, arr in extracted.covariates.items():
            predictors.append(arr.astype(float))
            names.append(name)
        if not predictors:
            raise BusinessValidationError("At least one predictor required.")
        y = frame[extracted.outcome_name].cast(pl.Float64).drop_nulls()
        x_df = frame.select([extracted.outcome_name] + names).drop_nulls()
        y_arr = x_df[extracted.outcome_name].to_numpy()
        x_arr = x_df.select(names).to_numpy()
        x_const = sm.add_constant(x_arr)
        model = sm.OLS(y_arr, x_const).fit()
        return self._regression_result(StatisticalTestType.MULTIPLE_LINEAR_REGRESSION, model, alpha, names)

    def _logistic_regression(
        self, frame: pl.DataFrame, extracted: ExtractedData, alpha: float, ref: float | None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        if extracted.outcome_name is None or extracted.predictor_name is None:
            raise BusinessValidationError("Logistic regression requires outcome and predictor.")
        df = frame.select([extracted.outcome_name, extracted.predictor_name]).drop_nulls()
        y_raw = df[extracted.outcome_name]
        if is_numeric(y_raw.dtype):
            y = y_raw.cast(pl.Float64).to_numpy()
        else:
            cats = y_raw.unique().sort()
            if cats.len() != 2:
                raise BusinessValidationError("Logistic regression requires binary outcome.")
            mapping = {cats[0]: 0, cats[1]: 1}
            y = np.array([mapping[v] for v in y_raw.to_list()])
        x = sm.add_constant(df[extracted.predictor_name].cast(pl.Float64).to_numpy())
        model = sm.Logit(y, x).fit(disp=0)
        odds = {extracted.predictor_name: float(np.exp(model.params[1]))}
        return (
            StatisticalTestResultDTO(
                test_type=StatisticalTestType.LOGISTIC_REGRESSION,
                statistic=float(model.llr), p_value=float(model.llr_pvalue),
                degrees_of_freedom=float(model.df_model),
                is_significant=model.llr_pvalue < alpha, alpha=alpha,
                details={"pseudo_r_squared": float(model.prsquared), "odds_ratios": odds},
            ),
            {"odds_ratios": odds, "r_squared": float(model.prsquared)},
        )

    @staticmethod
    def _two_groups(extracted: ExtractedData) -> tuple[np.ndarray, np.ndarray]:
        if extracted.outcome is None or extracted.grouping is None:
            raise BusinessValidationError("Two-group test requires outcome and grouping variables.")
        groups = np.unique(extracted.grouping)
        if len(groups) != 2:
            raise BusinessValidationError("Exactly two groups required.")
        g1 = extracted.outcome[extracted.grouping == groups[0]].astype(float)
        g2 = extracted.outcome[extracted.grouping == groups[1]].astype(float)
        return g1, g2

    @staticmethod
    def _pair_numeric(extracted: ExtractedData) -> tuple[np.ndarray, np.ndarray]:
        if extracted.outcome is None or extracted.predictor is None:
            raise BusinessValidationError("Requires numeric outcome and predictor.")
        x = extracted.predictor.astype(float)
        y = extracted.outcome.astype(float)
        n = min(len(x), len(y))
        return x[:n], y[:n]

    @staticmethod
    def _contingency_table(frame: pl.DataFrame, extracted: ExtractedData) -> tuple[np.ndarray, float]:
        if extracted.outcome_name is None or extracted.predictor_name is None:
            raise BusinessValidationError("Contingency test requires two categorical variables.")
        ct = frame.group_by([extracted.outcome_name, extracted.predictor_name]).len().pivot(
            on=extracted.predictor_name,
            index=extracted.outcome_name,
            values="len",
        ).fill_null(0)
        table = ct.select(pl.all().exclude(extracted.outcome_name)).to_numpy()
        n = table.sum()
        r, k = table.shape
        chi2 = stats.chi2_contingency(table)[0] if n > 0 and min(r, k) > 1 else 0.0
        cramers = float(np.sqrt(chi2 / (n * (min(r, k) - 1)))) if n > 0 and min(r, k) > 1 else 0.0
        return table, cramers

    @staticmethod
    def _ttest_result(
        test_type: StatisticalTestType,
        stat: float,
        p: float,
        df: float | None,
        alpha: float,
        extra: dict,
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        return (
            StatisticalTestResultDTO(
                test_type=test_type,
                statistic=float(stat), p_value=float(p), degrees_of_freedom=df,
                is_significant=p < alpha, alpha=alpha, details=extra,
            ),
            extra,
        )

    @staticmethod
    def _correlation_result(
        test_type: StatisticalTestType, r: float, p: float, n: int, alpha: float
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        details = {"correlation": float(r), "n": n}
        return (
            StatisticalTestResultDTO(
                test_type=test_type,
                statistic=float(r), p_value=float(p), degrees_of_freedom=float(n - 2),
                is_significant=p < alpha, alpha=alpha, details=details,
            ),
            details,
        )

    @staticmethod
    def _regression_result(
        test_type: StatisticalTestType, model: Any, alpha: float, names: list[str] | None = None
    ) -> tuple[StatisticalTestResultDTO, dict[str, Any]]:
        coef_names = names or ["predictor"]
        coefficients = []
        coef_cis = []
        for i, name in enumerate(["intercept"] + coef_names):
            if i >= len(model.params):
                break
            pval = float(model.pvalues[i])
            coefficients.append({
                "name": name,
                "estimate": float(model.params[i]),
                "std_error": float(model.bse[i]),
                "t_statistic": float(model.tvalues[i]),
                "p_value": pval,
                "significant": pval < alpha,
            })
            ci = model.conf_int().iloc[i]
            coef_cis.append({"name": name, "lower": float(ci[0]), "upper": float(ci[1])})
        details = {
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "f_statistic": float(model.fvalue) if model.fvalue is not None else None,
            "f_p_value": float(model.f_pvalue) if model.f_pvalue is not None else None,
            "coefficients": coefficients,
            "coefficient_cis": coef_cis,
            "residual_std": float(np.std(model.resid)),
        }
        return (
            StatisticalTestResultDTO(
                test_type=test_type,
                statistic=float(model.fvalue) if model.fvalue is not None else None,
                p_value=float(model.f_pvalue) if model.f_pvalue is not None else None,
                degrees_of_freedom=float(model.df_model),
                is_significant=(model.f_pvalue or 1) < alpha,
                alpha=alpha,
                details=details,
            ),
            details,
        )
