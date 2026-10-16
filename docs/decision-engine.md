# Decision Intelligence Engine (Phase 8)

Delphi's Decision Intelligence Engine transforms statistical evidence, causal estimates, counterfactual simulations, business constraints, and uncertainty into **ranked, explainable recommendations**.

This is **not** an LLM feature, rule engine, or black-box AI. Every recommendation traces an evidence chain:

```
Statistical Evidence → Causal Evidence → Simulation → Constraints → Risk → Optimization → Recommendation
```

## Architecture

```
DecisionEngine (Orchestrator)
  → ObjectiveAnalyzer
  → ConstraintManager
  → DecisionScorer
  → RecommendationGenerator
  → DecisionValidator
  → OptimizationEngine
  → TradeoffEngine
  → PriorityEngine
  → ExplanationEngine
  → Persistence (DecisionRun)
```

## Scoring methodology

Composite score (documented in `DecisionScorer.METHODOLOGY`):

| Component | Weight |
|-----------|--------|
| Business impact | 25% |
| ROI | 20% |
| Confidence | 20% |
| Risk (inverse) | 15% |
| Feasibility | 10% |
| Strategic alignment | 10% |

Multiplied by constraint satisfaction factor. Weak recommendations are rejected or deferred.

## API

| Method | Path |
|--------|------|
| POST | `/api/v1/decisions/analyze` |
| GET | `/api/v1/decisions?dataset_id=` |
| GET | `/api/v1/decisions/{id}` |
| GET | `/api/v1/recommendations?decision_id=` |
| GET | `/api/v1/tradeoffs?decision_id=` |
| GET | `/api/v1/priorities?decision_id=` |
| GET | `/api/v1/objectives` |

## References

- Keeney, R. L. (1992). *Value-Focused Thinking*.
- Howard, R. A. (1988). Decision analysis: practice and promise.
- Pearl, J. (2009). *Causality* — evidence hierarchies for causal claims.
