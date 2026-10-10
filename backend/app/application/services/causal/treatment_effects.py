"""Treatment effect estimation engine."""

from __future__ import annotations

import numpy as np
import polars as pl
import statsmodels.api as sm
from scipy import stats
from statsmodels.discrete.discrete_model import Logit

from app.application.dto.causal import TreatmentEffectDTO
from app.application.services.statistics.data_extractor import is_numeric
from app.domain.value_objects.causal import CausalEstimatorType
from app.shared.exceptions import BusinessValidationError


class TreatmentEffectEngine:
    """Estimate ATE, ATT, ATC using multiple estimators."""

    def estimate(
        self,
        *,
        frame: pl.DataFrame,
        treatment: str,
        outcome: str,
        estimator: CausalEstimatorType,
        adjustment_set: tuple[str, ...],
        confidence_level: float = 0.95,
    ) -> TreatmentEffectDTO:
        handlers = {
            CausalEstimatorType.DIFFERENCE_IN_MEANS: self._difference_in_means,
            CausalEstimatorType.REGRESSION_ADJUSTMENT: self._regression_adjustment,
            CausalEstimatorType.INVERSE_PROBABILITY_WEIGHTING: self._ipw,
            CausalEstimatorType.PROPENSITY_SCORE_MATCHING: self._psm,
            CausalEstimatorType.DOUBLE_MACHINE_LEARNING: self._dml_foundation,
        }
        handler = handlers.get(estimator, self._difference_in_means)
        return handler(frame, treatment, outcome, adjustment_set, confidence_level)

    def _prepare_binary_treatment(self, series: pl.Series) -> tuple[np.ndarray, dict]:
        if is_numeric(series.dtype):
            vals = series.to_numpy()
            median = float(np.median(vals))
            return (vals > median).astype(float), {"threshold": median}
        cats = series.unique().sort().to_list()
        if len(cats) != 2:
            raise BusinessValidationError(
                "Binary treatment required for this estimator. Use numeric or 2-level categorical."
            )
        mapping = {cats[0]: 0.0, cats[1]: 1.0}
        return np.array([mapping[v] for v in series.to_list()]), {"mapping": mapping}

    def _difference_in_means(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], confidence_level: float,
    ) -> TreatmentEffectDTO:
        df = frame.select([treatment, outcome]).drop_nulls()
        t, _ = self._prepare_binary_treatment(df[treatment])
        y = df[outcome].cast(pl.Float64).to_numpy()
        t1, t0 = y[t == 1], y[t == 0]
        if len(t1) < 2 or len(t0) < 2:
            raise BusinessValidationError("Insufficient observations in treatment groups.")
        ate = float(t1.mean() - t0.mean())
        se = float(np.sqrt(t1.var(ddof=1) / len(t1) + t0.var(ddof=1) / len(t0)))
        return self._build_result(
            CausalEstimatorType.DIFFERENCE_IN_MEANS, ate, ate, -ate, se, confidence_level,
            {"n_treated": len(t1), "n_control": len(t0)},
        )

    def _regression_adjustment(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], confidence_level: float,
    ) -> TreatmentEffectDTO:
        cols = [treatment, outcome, *adjustment_set]
        df = frame.select([c for c in cols if c in frame.columns]).drop_nulls()
        t, meta = self._prepare_binary_treatment(df[treatment])
        y = df[outcome].cast(pl.Float64).to_numpy()
        if adjustment_set:
            x_adj = df.select(list(adjustment_set)).cast(pl.Float64).to_numpy()
            x = np.column_stack([t, x_adj])
        else:
            x = t.reshape(-1, 1)
        x_const = sm.add_constant(x)
        model = sm.OLS(y, x_const).fit()
        ate = float(model.params[1])
        se = float(model.bse[1])
        return self._build_result(
            CausalEstimatorType.REGRESSION_ADJUSTMENT, ate, ate, ate, se, confidence_level,
            {"r_squared": float(model.rsquared), "adjustment_set": list(adjustment_set), **meta},
        )

    def _ipw(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], confidence_level: float,
    ) -> TreatmentEffectDTO:
        cols = [treatment, outcome, *adjustment_set]
        df = frame.select([c for c in cols if c in frame.columns]).drop_nulls()
        t, meta = self._prepare_binary_treatment(df[treatment])
        y = df[outcome].cast(pl.Float64).to_numpy()
        if adjustment_set:
            x = df.select(list(adjustment_set)).cast(pl.Float64).to_numpy()
        else:
            x = np.ones((len(t), 1))
        ps_model = Logit(t, sm.add_constant(x)).fit(disp=0)
        ps = ps_model.predict(sm.add_constant(x))
        ps = np.clip(ps, 0.05, 0.95)
        weights_t = t / ps + (1 - t) / (1 - ps)
        y1 = np.average(y, weights=t / ps)
        y0 = np.average(y, weights=(1 - t) / (1 - ps))
        ate = float(y1 - y0)
        boot_ates = []
        rng = np.random.default_rng(42)
        for _ in range(200):
            idx = rng.choice(len(t), len(t), replace=True)
            bt, by, bps = t[idx], y[idx], ps[idx]
            bps = np.clip(bps, 0.05, 0.95)
            by1 = np.average(by, weights=bt / bps)
            by0 = np.average(by, weights=(1 - bt) / (1 - bps))
            boot_ates.append(by1 - by0)
        se = float(np.std(boot_ates, ddof=1))
        att = float(np.mean(y[t == 1]) - np.average(y, weights=(1 - t) / (1 - ps)))
        atc = float(np.average(y, weights=t / ps) - np.mean(y[t == 0]))
        return self._build_result(
            CausalEstimatorType.INVERSE_PROBABILITY_WEIGHTING, ate, att, atc, se, confidence_level,
            {"mean_propensity": float(ps.mean()), "adjustment_set": list(adjustment_set), **meta},
        )

    def _psm(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], confidence_level: float,
    ) -> TreatmentEffectDTO:
        cols = [treatment, outcome, *adjustment_set]
        df = frame.select([c for c in cols if c in frame.columns]).drop_nulls()
        t, meta = self._prepare_binary_treatment(df[treatment])
        y = df[outcome].cast(pl.Float64).to_numpy()
        if adjustment_set:
            x = df.select(list(adjustment_set)).cast(pl.Float64).to_numpy()
        else:
            x = np.random.default_rng(42).normal(size=(len(t), 1))
        ps_model = Logit(t, sm.add_constant(x)).fit(disp=0)
        ps = ps_model.predict(sm.add_constant(x))
        treated_idx = np.where(t == 1)[0]
        control_idx = np.where(t == 0)[0]
        if len(treated_idx) == 0 or len(control_idx) == 0:
            return self._build_result(
                CausalEstimatorType.PROPENSITY_SCORE_MATCHING,
                0.0, 0.0, 0.0, 0.0, confidence_level,
                {
                    "n_matched": 0,
                    "adjustment_set": list(adjustment_set),
                    "warning": "Insufficient treated or control units for matching.",
                    **meta,
                },
            )
        matched_controls = []
        for i in treated_idx:
            distances = np.abs(ps[control_idx] - ps[i])
            matched_controls.append(control_idx[np.argmin(distances)])
        matched_y1 = y[treated_idx]
        matched_y0 = y[matched_controls]
        ate = float(matched_y1.mean() - matched_y0.mean())
        se = float(np.sqrt(matched_y1.var(ddof=1) / len(matched_y1) + matched_y0.var(ddof=1) / len(matched_y0)))
        return self._build_result(
            CausalEstimatorType.PROPENSITY_SCORE_MATCHING, ate, ate, -ate, se, confidence_level,
            {"n_matched": len(treated_idx), "adjustment_set": list(adjustment_set), **meta},
        )

    def _dml_foundation(
        self, frame: pl.DataFrame, treatment: str, outcome: str,
        adjustment_set: tuple[str, ...], confidence_level: float,
    ) -> TreatmentEffectDTO:
        """Foundation DML via residual-on-residual regression (partialing out confounders)."""
        result = self._regression_adjustment(frame, treatment, outcome, adjustment_set, confidence_level)
        return TreatmentEffectDTO(
            estimator=CausalEstimatorType.DOUBLE_MACHINE_LEARNING,
            ate=result.ate, att=result.att, atc=result.atc,
            std_error=result.std_error,
            confidence_level=confidence_level,
            ci_lower=result.ci_lower, ci_upper=result.ci_upper,
            p_value=result.p_value,
            details={**result.details, "note": "Foundation DML via partial regression."},
        )

    @staticmethod
    def _build_result(
        estimator: CausalEstimatorType,
        ate: float, att: float, atc: float,
        se: float, confidence_level: float,
        details: dict,
    ) -> TreatmentEffectDTO:
        z = stats.norm.ppf(1 - (1 - confidence_level) / 2)
        ci_lo = ate - z * se
        ci_hi = ate + z * se
        p_value = float(2 * (1 - stats.norm.cdf(abs(ate / se)))) if se > 0 else None
        return TreatmentEffectDTO(
            estimator=estimator,
            ate=ate, att=att, atc=atc,
            std_error=se,
            confidence_level=confidence_level,
            ci_lower=ci_lo, ci_upper=ci_hi,
            p_value=p_value,
            details=details,
        )
