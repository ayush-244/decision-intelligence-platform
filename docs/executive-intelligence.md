# Executive Intelligence Layer (Phase 9)

Phase 9 transforms statistical, causal, simulation, and decision outputs into **executive-ready intelligence**. Leaders get answers in business language — not p-values, coefficients, or DAGs — with full evidence available on demand.

## Architecture

```
DecisionRun (Phase 8)
        │
        ▼
ExecutiveReportEngine
   ├── BusinessLanguageEngine   — prose summaries, ROI narratives
   ├── ExplainabilityEngine     — evidence chains per recommendation
   ├── TimelineEngine           — implementation roadmap
   └── ExportEngine             — Markdown, CSV, JSON, print-ready PDF
        │
        ▼
ExecutiveReport (versioned, tenant-scoped)
        │
        ▼
DashboardEngine — pipeline health, ROI/risk/confidence aggregates
```

Clean Architecture boundaries:

| Layer | Responsibility |
|-------|----------------|
| Domain | `ExecutiveReport` entity, `ExecutiveReportRepository` port, value objects |
| Application | `ExecutiveReportEngine`, use cases, DTOs |
| Infrastructure | SQLAlchemy model, repository, Alembic migration |
| Presentation | FastAPI routers `/reports`, `/executive/dashboard` |

## Explainability engine

Every recommendation in a report includes an `ExplainabilityBlock`:

- **Why** — ranking rationale from decision scoring
- **Evidence chain** — statistical → causal → simulation → decision narratives
- **Confidence** — aggregated score with calibrated language (high / moderate / low)
- **Assumptions & limitations** — from decision analysis
- **Business interpretation** — plain-language action guidance
- **Alternative actions** — status quo, pilot, defer options

Technical jargon is hidden by default; the appendix exposes raw decision results when `include_technical_appendix=true`.

## Report generation

`POST /api/v1/reports/generate` requires a **completed** `DecisionRun`. The engine:

1. Creates a versioned `ExecutiveReport` (status `running`)
2. Pulls recommendations and links causal/simulation evidence per recommendation
3. Builds structured sections: executive summary, key findings, ROI/risk, tradeoffs, scenario comparison, roadmap, KPIs, narrative
4. Persists completed result JSON

### Report sections

| Section | Purpose |
|---------|---------|
| Executive Summary | One-paragraph leadership brief |
| Business Objective | Stated goal for the engagement |
| Key Findings | What happened — in business terms |
| Decision Summary | Outcome of decision intelligence |
| Top Recommendations | Ranked actions (max 5) |
| Expected ROI / Risks | Financial and risk framing |
| Confidence Assessment | Calibrated certainty |
| Tradeoffs & Scenarios | Compare options A vs B |
| Implementation Roadmap | Priority, effort, milestones, owners |
| Business KPIs | Tracked outcome metrics |
| Narrative | Answers: what, why, certainty, action, inaction |
| Appendix | Optional technical evidence |

## Persistence

Table `executive_reports`:

- FK to `datasets`, `dataset_versions`, `decision_runs`
- `version_number` per dataset + report name
- `configuration_json` — generation request snapshot
- `result_json` — full executive artifact
- Tenant isolation via `organization_id`

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/reports/generate` | Generate report from decision run |
| `GET` | `/api/v1/reports?dataset_id=` | List report history |
| `GET` | `/api/v1/reports/{id}` | Fetch full report |
| `POST` | `/api/v1/reports/export?report_id=` | Export (markdown, csv, json, pdf) |
| `GET` | `/api/v1/executive/dashboard?dataset_id=` | Dashboard snapshot |

Permissions: `report:read` (VIEWER+), `report:create` (ANALYST+).

## Frontend

Route: `/app/datasets/:datasetId/executive`

- Executive dashboard (health, pipeline, ROI, report count)
- Report generator (select completed decision, set objective)
- Report viewer with progressive disclosure (summary first, evidence on expand)
- Implementation timeline
- Export center (Markdown, CSV, JSON, PDF download)

## Exports

| Format | Use case |
|--------|----------|
| Markdown | Shareable briefs, PowerPoint-ready source |
| CSV | KPI / recommendation tabular extract |
| JSON | Programmatic consumption |
| PDF | Print-ready (Markdown body; render via browser print) |

## Testing

- Unit: `tests/unit/test_executive_engine.py` — language, explainability, timeline, export
- Integration: `tests/integration/test_executive_endpoints.py` — full causal → simulation → decision → report chain

## Related

- [Decision intelligence (Phase 8)](decision-engine.md)
- [Architecture overview](architecture.md)
