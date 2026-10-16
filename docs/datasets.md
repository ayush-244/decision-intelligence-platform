# Dataset Ingestion & Lifecycle (Phase 3)

Phase 3 establishes versioned, validated tabular datasets as first-class platform resources.

## Architecture

```
Upload (multipart)
    → FileValidator (size, format, empty check)
    → StorageProvider.store (LocalStorage → future S3/Azure/GCS)
    → TabularProcessor.profile (Polars: schema + preview sample)
    → Persist DatasetVersion + SchemaSnapshot + ValidationReport
    → Update Dataset.current_version_id
```

### Why DatasetVersion is the analysis anchor

Future profiling, causal inference, and simulation modules reference a **DatasetVersion ID**, not the logical Dataset ID. This guarantees reproducibility: re-running an analysis against `v3` always uses the same bytes and schema hash, even if `v4` exists.

### Storage abstraction

| Layer | Responsibility |
|-------|----------------|
| `StorageProvider` (port) | Store/read/delete blobs by opaque key |
| `LocalStorageProvider` | Filesystem under `DELPHI_STORAGE_BASE_PATH` |
| Future adapters | S3, Azure Blob, GCS — swap in `deps.py` only |

Key layout: `{org_id}/{project_id}/{dataset_id}/v{N}/{filename}`

### Entity model

| Entity | Purpose |
|--------|---------|
| **Dataset** | Stable user-facing identity within a project |
| **DatasetVersion** | Immutable snapshot (hash, row/col counts, storage key) |
| **DatasetFile** | Physical artifact metadata per version |
| **UploadJob** | Lifecycle tracking (sync today, async-ready) |
| **SchemaSnapshot** | Frozen column metadata at ingest |
| **ValidationReport** | Structured validation outcome |
| **DatasetStatistics** | Profiling placeholder (Phase 4+) |

## Ingestion pipeline stages

1. **Receive** — multipart upload via API
2. **Validate** — type, size, emptiness, MIME warnings
3. **Store** — write blob via `StorageProvider`
4. **Hash** — SHA-256 for deduplication detection
5. **Profile** — Polars lazy scan (CSV/Parquet) or read (XLSX) with row cap
6. **Infer schema** — semantic types, null %, distinct counts, examples
7. **Persist** — version row, file row, schema, validation, statistics stub
8. **Respond** — dataset + version + preview rows + validation status

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/datasets/upload` | New dataset (multipart: `project_id`, `file`, optional `name`) |
| GET | `/api/v1/datasets?project_id=` | List datasets |
| GET | `/api/v1/datasets/{id}` | Dataset detail |
| GET | `/api/v1/datasets/{id}/versions` | Version history |
| GET | `/api/v1/datasets/{id}/preview` | Row/column preview |
| DELETE | `/api/v1/datasets/{id}` | Soft delete |
| POST | `/api/v1/datasets/{id}/new-version` | Upload replacement version |

All routes require JWT + `X-Organization-ID` and enforce RBAC (`dataset:*` permissions).

## Schema inference

Semantic types extend beyond raw dtypes:

- `integer`, `float`, `boolean`, `datetime`, `text`, `categorical`, `identifier`, `ordinal` (reserved)

Inference uses Polars dtypes plus heuristics (cardinality, uniqueness). Designed as a pipeline stage so ML-based inference can plug in later.

## Migration

```bash
cd backend && uv run alembic upgrade head
```

Revision: `20250706160000_phase3_datasets.py`

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DELPHI_STORAGE_BASE_PATH` | `./data/storage` | Local blob root |
| `DELPHI_MAX_UPLOAD_SIZE_BYTES` | `104857600` | 100 MiB |
| `DELPHI_PREVIEW_ROW_LIMIT` | `50` | API preview rows |
| `DELPHI_PREVIEW_SAMPLE_ROWS` | `10000` | Max rows scanned for inference |
