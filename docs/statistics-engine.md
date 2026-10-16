# Statistical Analysis Engine (Phase 5)

Delphi's Statistical Analysis Engine is a production-grade, explainable analytics core
anchored to **dataset versions**. It recommends appropriate methods, validates assumptions,
executes tests, computes effect sizes and confidence intervals, and returns business-ready
interpretations—not raw p-values alone.

## Architecture

```
Analysis Orchestrator (StatisticsEngine)
    → Assumption Validation Engine (AssumptionValidator)
    → Statistical Test Selector (StatisticalTestSelector)
    → Statistical Execution Engine (StatisticalExecutor)
    → Effect Size Calculator (EffectSizeCalculator)
    → Confidence Interval Engine (ConfidenceIntervalEngine)
    → Regression Engine (RegressionEngine)
    → Result Interpreter (ResultInterpreter)
    → Persistence (StatisticalAnalysisRun)
```

Each component has a single responsibility and is independently testable. New tests are added
by extending `StatisticalTestType` and registering an executor handler—existing modules remain
unchanged (Open-Closed Principle).

## Supported analyses

| Category | Methods |
|----------|---------|
| Descriptive | Summary statistics (numeric & categorical) |
| Parametric tests | One-sample, independent, paired, Welch t-tests; one-way ANOVA |
| Non-parametric | Mann-Whitney U, Wilcoxon signed-rank |
| Association | Pearson, Spearman, Kendall correlations; chi-square; Fisher's exact |
| Regression | Simple & multiple OLS; logistic regression (foundation) |

## Assumption validation

Before execution, the engine checks applicable assumptions:

- Normality (Shapiro-Wilk)
- Equal variances (Levene)
- Sample size adequacy
- Expected cell frequencies (chi-square)
- Linearity (correlation strength proxy)
- Multicollinearity (inter-predictor correlation / VIF path)
- Missing data impact
- Independence (documented, design-based)

Failed assumptions trigger **alternative recommendations** (e.g. independent t-test → Mann-Whitney U
or Welch t-test) with documented reasoning.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/statistics/analyze` | Run analysis |
| GET | `/api/v1/statistics/{analysisId}` | Fetch result |
| GET | `/api/v1/statistics/history?dataset_id=` | List history |
| POST | `/api/v1/statistics/recommendations` | Get test recommendation |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DELPHI_STATISTICS_SIGNIFICANCE_LEVEL` | 0.05 | Alpha for hypothesis tests |
| `DELPHI_STATISTICS_CONFIDENCE_LEVEL` | 0.95 | Default CI level |
| `DELPHI_STATISTICS_SAMPLE_ROWS` | 100000 | Max rows sampled |

## References

- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*.
- Shapiro, S. S., & Wilk, M. B. (1965). Biometrika.
- Levene, H. (1960). Contributions to Probability and Statistics.
- Pearson, K. (1895). Philosophical Transactions of the Royal Society.
- Fisher, R. A. (1922). Journal of the Royal Statistical Society.
