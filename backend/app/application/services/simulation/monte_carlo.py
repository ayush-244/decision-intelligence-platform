"""Monte Carlo uncertainty propagation for simulations."""

from __future__ import annotations

import numpy as np

from app.application.dto.simulation import CounterfactualOutcomeDTO, MonteCarloResultDTO


class MonteCarloEngine:
    """Repeated sampling around counterfactual point estimates."""

    def simulate(
        self,
        *,
        counterfactual: CounterfactualOutcomeDTO,
        std_error: float,
        iterations: int,
        seed: int = 42,
    ) -> MonteCarloResultDTO:
        rng = np.random.default_rng(seed)
        mean = counterfactual.expected_outcome
        sigma = max(std_error, abs(mean) * 0.05, 1e-6)
        samples = rng.normal(loc=mean, scale=sigma, size=iterations)
        p05, p25, p75, p95 = np.percentile(samples, [5, 25, 75, 95])
        tail_risk = float(np.mean(samples < counterfactual.baseline_outcome))
        return MonteCarloResultDTO(
            iterations=iterations,
            expected_value=float(np.mean(samples)),
            median=float(np.median(samples)),
            p05=float(p05),
            p25=float(p25),
            p75=float(p75),
            p95=float(p95),
            tail_risk=round(tail_risk, 4),
            distribution=tuple(round(float(v), 6) for v in samples[:200]),
            methodology=(
                "Parametric Monte Carlo: outcome ~ Normal(expected, std_error) "
                "with std_error from causal estimate."
            ),
        )
