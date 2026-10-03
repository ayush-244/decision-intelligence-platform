"""Enterprise infrastructure value objects."""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class JobType(StrEnum):
    DATASET_PROCESSING = "dataset_processing"
    DATA_INTELLIGENCE = "data_intelligence"
    STATISTICS = "statistics"
    CAUSAL_ANALYSIS = "causal_analysis"
    SIMULATION = "simulation"
    DECISION = "decision"
    EXECUTIVE_REPORT = "executive_report"


class CacheNamespace(StrEnum):
    DATASET_METADATA = "dataset_metadata"
    SCHEMA = "schema"
    ANALYSIS = "analysis"
    SIMULATION = "simulation"
    RECOMMENDATION = "recommendation"
    DASHBOARD = "dashboard"
    SEARCH = "search"


# Default TTL seconds per namespace — version-aware keys prevent stale reads.
CACHE_TTL_SECONDS: dict[CacheNamespace, int] = {
    CacheNamespace.DATASET_METADATA: 3600,
    CacheNamespace.SCHEMA: 7200,
    CacheNamespace.ANALYSIS: 1800,
    CacheNamespace.SIMULATION: 1800,
    CacheNamespace.RECOMMENDATION: 900,
    CacheNamespace.DASHBOARD: 300,
    CacheNamespace.SEARCH: 120,
}
