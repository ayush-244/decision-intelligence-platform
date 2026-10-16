# Unified Decision Workspace (Phase 10)

Phase 10 introduces the **primary interface** for Delphi — a cohesive analytics operating system where analysts complete the full journey from data intelligence through executive reporting without disconnected page hops.

## Workspace architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Global nav · Command palette (⌘K) · Global search         │
├──────────┬──────────────────────────────┬───────────────────┤
│ Session  │ Analysis canvas              │ Knowledge timeline│
│ sidebar  │ (linked analysis modules)    │ + comments        │
│ Workflow │ Comparison workspace         │ Activity feed     │
│ progress │ Context / evidence drawer    │                   │
└──────────┴──────────────────────────────┴───────────────────┘
```

| Layer | Responsibility |
|-------|----------------|
| **DecisionSession** | Links dataset version → statistics → DAG → causal → simulation → decision → report |
| **SessionActivity** | Chronological events + collaboration foundation (comments, mentions metadata) |
| **WorkspaceSearchEngine** | Tenant-scoped search across projects, datasets, analyses, sessions |
| **TimelineEngine** | Aggregates session activities + linked artifact metadata |
| **ComparisonEngine** | Side-by-side session comparison (ROI, confidence, workflow step) |

Frontend route: `/app/workspace/:datasetId`

## DecisionSession model

A `DecisionSession` preserves the analytical journey:

- **Status:** `draft` · `active` · `paused` · `completed` · `archived`
- **Workflow step:** guided 11-step pipeline with visual progress
- **Artifact links:** optional FKs to statistical analysis, DAG, causal run, simulation, decision, executive report
- **Workspace state:** panel collapse, canvas nodes, comparison selection (JSON)
- **Versioning:** `version_number` per dataset + session name

Users can pause, resume, complete, and return to any prior step.

## Navigation

- **Dataset detail** → primary **Workspace** CTA
- **Analysis canvas** → deep-links to existing phase modules (intelligence, statistics, causal, simulation, decision, executive) with session context preserved
- **Command palette** (`⌘K` / `Ctrl+K`) → quick actions + global search
- Legacy per-module routes remain available for direct access

## Search architecture

`GET /api/v1/workspace/search?q=` queries:

- Projects (via workspace → project traversal)
- Datasets
- Statistical analyses, causal runs, simulations, decisions, reports (dataset-scoped)
- Decision sessions (name search)

Results are tenant-isolated, ranked by recency, and capped per resource type for scalability.

## APIs

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/sessions` | Create decision session |
| `GET` | `/api/v1/sessions?dataset_id=` | List sessions |
| `GET` | `/api/v1/sessions/{id}` | Get session + progress |
| `PATCH` | `/api/v1/sessions/{id}` | Update state, links, pause/resume/complete |
| `GET` | `/api/v1/sessions/{id}/timeline` | Knowledge timeline |
| `POST` | `/api/v1/sessions/{id}/comments` | Add comment (collaboration foundation) |
| `GET` | `/api/v1/workspace/search` | Global search |
| `POST` | `/api/v1/workspace/compare` | Compare two sessions |
| `GET` | `/api/v1/workspace/activity` | Audit / activity history |

Permissions: `session:read/create/update`, `workspace:search`, existing `workspace:read` for activity.

## Collaboration foundation

Prepared but not real-time:

- Session comments with mentions metadata
- Activity timeline per session
- Organization audit log exposure via `/workspace/activity`
- Shared link metadata in activity records

## Testing

- Unit: `tests/unit/test_workspace_engine.py`
- Integration: `tests/integration/test_workspace_endpoints.py`
- Frontend: workspace types + command palette patterns

## Related

- [Executive intelligence (Phase 9)](executive-intelligence.md)
- [Architecture overview](architecture.md)
