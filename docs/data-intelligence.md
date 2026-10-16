# Data Intelligence Engine (Phase 4)

Phase 4 turns uploaded datasets into **actionable data understanding** — not a simple profiling page, but an automated review resembling what an experienced data scientist would produce before any modeling work.

## Architecture

```
DatasetVersion (immutable anchor)
    ↓
DatasetFrameLoader (Polars lazy scan, row cap)
    ↓
Modular Analyzers (pure functions, independently testable)
    ↓
Scoring (weighted, explainable quality + health scores)
    ↓
IntelligenceEngine (orchestrator)
    ↓
IntelligenceReport (JSONB per version, cached)
    ↓
Slice APIs + Intelligence UI
```

### Why version-scoped reports

Like Phase 3 ingestion, intelligence is tied to **`DatasetVersion`**. Re-running analysis on v2 does not mutate v1's report. Future causal and simulation modules can reference both the dataset version and the intelligence report computed at that point in time.

### Report sections

| Section | Purpose |
|---------|---------|
| **Overview** | Trust headline, key findings, scores at a glance |
| **Data Quality** | Completeness, uniqueness, consistency, validity, integrity |
| **Schema Summary** | Column types and nullability snapshot |
| **Column Intelligence** | Per-column roles, usability, statistics, issues |
| **Distribution Analysis** | Histograms, shape, normality hints, transform suggestions |
| **Missing Data** | Column/row missingness, patterns, imputation hints |
| **Outlier Analysis** | IQR + Z-score detection (no automatic removal) |
| **Correlation Analysis** | Pearson/Spearman matrix, strong pairs, multicollinearity warnings |
| **Feature Relationships** | Numeric/categorical patterns worth investigating (not causation) |
| **Duplicate Analysis** | Row and column duplicate burden |
| **Data Health Score** | Explainable composite with category breakdown |
| **Analytical Readiness** | Regression/classification/clustering/causal suitability |
| **Recommendations** | Actionable next steps |

## Scoring methodology

### Data Quality Score (0–100)

Modular weighted components (configurable via `Settings.quality_score_weights`):

| Component | Default weight | Measures |
|-----------|----------------|----------|
| Completeness | 25% | Inverse of average null % |
| Uniqueness | 15% | Inverse of duplicate row % |
| Consistency | 20% | Constant/near-constant/mixed-type penalties |
| Validity | 20% | High-cardinality text, mixed types |
| Integrity | 20% | Likely identifiers without declared keys |

### Data Health Score (0–100)

Broader assessment including:

| Component | Default weight |
|-----------|----------------|
| Data quality | 30% |
| Missingness | 20% |
| Outliers | 15% |
| Column usability | 15% |
| Distributions | 10% |
| Cardinality | 10% |

Each component exposes **score + explanation** for transparency. Additional metrics can be plugged in without changing API contracts.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/datasets/{id}/intelligence/analyze` | Compute/regenerate report |
| GET | `/api/v1/datasets/{id}/intelligence` | Full report |
| GET | `/api/v1/datasets/{id}/summary` | Overview + health + readiness |
| GET | `/api/v1/datasets/{id}/quality` | Quality section only |
| GET | `/api/v1/datasets/{id}/columns` | Column intelligence |
| GET | `/api/v1/datasets/{id}/correlations` | Correlation analysis |
| GET | `/api/v1/datasets/{id}/outliers` | Outlier analysis |
| GET | `/api/v1/datasets/{id}/missing` | Missing data analysis |

Optional query: `?version_id=` (defaults to current version).

## Database

Table: `dataset_intelligence_reports` — one row per `version_id`, `report_json` JSONB.

Migration: `20250708160000_phase4_intelligence.py`

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DELPHI_INTELLIGENCE_SAMPLE_ROWS` | `100000` | Max rows sampled for analysis |
| `DELPHI_INTELLIGENCE_CORRELATION_MAX_COLUMNS` | `30` | Cap on correlation matrix width |
| `DELPHI_OUTLIER_ZSCORE_THRESHOLD` | `3.0` | Z-score outlier threshold |

## Performance notes

- Polars lazy scans for CSV/Parquet; row cap prevents full memory load
- Correlation matrix capped for wide datasets
- Reports cached in PostgreSQL — expensive compute runs once per version until re-analyzed
- Architecture supports future background workers (status field: `pending` → `computing` → `completed`)

## Frontend

Access via **Dataset detail → Intelligence** or `/app/datasets/{id}/intelligence`.

Tabs: Summary, Data Quality, Column Explorer, Correlations, Missing Data, Outliers, Distributions.

Visualizations: Apache ECharts heatmaps and histograms.
