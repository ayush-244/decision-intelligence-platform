# Causal Inference Engine (Phase 6)

Delphi's Causal Inference Engine helps users discover, model, estimate, validate, and explain **causal** relationships — not mere correlations.

## Design principles

- **Never claim causality without assumptions** — every report lists required assumptions and limitations
- **Stable public API** — third-party libraries (NetworkX, statsmodels) sit behind `CausalGraphPort` and internal estimators
- **Reproducibility** — every run is versioned and anchored to a `DatasetVersion` and optional `DAGVersion`
- **Transparency over automation** — identification failures and refutation results are surfaced explicitly

## Architecture

```
CausalEngine (Orchestrator)
  → VariableRoleAnalyzer
  → DAGManager
  → CausalAssumptionValidator
  → IdentificationEngine (backdoor criterion via d-separation)
  → EstimatorSelector
  → TreatmentEffectEngine (ATE, ATT, ATC)
  → RefutationEngine
  → SensitivityEngine
  → CausalInterpreter
  → Persistence (CausalAnalysisRun, DAGVersion)
```

## Supported capabilities

| Area | Status |
|------|--------|
| DAG create/edit/validate/version | ✓ |
| Variable role classification | ✓ (heuristic + override) |
| Backdoor identification | ✓ |
| Frontdoor / IV | Architecture prepared |
| ATE, ATT, ATC | ✓ |
| IPW, PSM, regression adjustment | ✓ |
| DML foundation | ✓ |
| Refutation (random cause, placebo, subset) | ✓ |
| Sensitivity analysis | ✓ |
| Explainable causal reports | ✓ |

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/causal/analyze` |
| GET | `/api/v1/causal/{analysisId}` |
| GET | `/api/v1/causal/history?dataset_id=` |
| POST | `/api/v1/causal/dag` |
| PUT | `/api/v1/causal/dag/{id}` |
| GET | `/api/v1/causal/dag/{id}` |
| POST | `/api/v1/causal/refute?analysis_id=` |
| GET | `/api/v1/causal/sensitivity?analysis_id=` |

## References

- Pearl, J. (2009). *Causality*.
- Rosenbaum, P. R., & Rubin, D. B. (1983). Biometrika — propensity scores.
- Imbens, G. W., & Rubin, D. B. (2015). *Causal Inference for Statistics, Social, and Biomedical Sciences*.
- Chernozhukov, V. et al. (2018). *The Econometrics Journal* — double/debiased machine learning.
