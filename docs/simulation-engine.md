# Decision Simulation Engine (Phase 7)

Delphi's Simulation Engine estimates the **likely consequences of hypothetical business interventions** using causal models from Phase 6. This is counterfactual decision analysis — not forecasting or predictive ML.

## Design principles

- **Causal grounding** — every simulation references a completed `CausalAnalysisRun`
- **Transparency** — assumptions, limitations, uncertainty, and extrapolation warnings are always exposed
- **Not guarantees** — Monte Carlo distributions and risk scores communicate uncertainty
- **Reproducibility** — runs are versioned and anchored to `DatasetVersion`, causal, and optional statistical analyses

## Architecture

```
SimulationEngine (Orchestrator)
  → InterventionValidator
  → TreatmentEffectIntegrator (Phase 6)
  → CounterfactualGenerator
  → MonteCarloEngine
  → ConstraintEngine
  → RiskEngine
  → ROICalculator
  → ScenarioComparator
  → SimulationInterpreter
  → Persistence (SimulationScenario, SimulationRun)
```

## Capabilities

| Area | Status |
|------|--------|
| Scenario builder (create, version, clone) | ✓ |
| Numeric / categorical / boolean interventions | ✓ |
| Counterfactual outcomes + CI | ✓ |
| Monte Carlo simulation | ✓ |
| Business constraints (budget, ROI, capacity) | ✓ |
| Risk assessment | ✓ |
| ROI / cost-benefit | ✓ |
| Explainable simulation reports | ✓ |
| Scenario comparison (foundation) | ✓ |

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/simulations` |
| GET | `/api/v1/simulations/{id}` |
| GET | `/api/v1/simulations/history?dataset_id=` |
| POST | `/api/v1/scenarios` |
| PUT | `/api/v1/scenarios/{id}` |
| GET | `/api/v1/scenarios?dataset_id=` |
| GET | `/api/v1/scenarios/{id}` |
| POST | `/api/v1/roi` |
| POST | `/api/v1/risk` |

## Methodology

1. Load causal treatment effect (ATE/ATT) from Phase 6
2. Validate interventions against observed data ranges
3. Project counterfactual outcome: `baseline + ATE × intervention_scale`
4. Propagate uncertainty via parametric Monte Carlo
5. Evaluate business constraints and aggregate risk
6. Compute ROI from configurable unit economics

## References

- Pearl, J. & Mackenzie, D. (2018). *The Book of Why* — counterfactual reasoning.
- Imbens, G. W., & Rubin, D. B. (2015). *Causal Inference* — potential outcomes framework.
- Morgan, S. L., & Winship, C. (2015). *Counterfactuals and Causal Inference*.
