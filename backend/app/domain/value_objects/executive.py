"""Executive intelligence value objects."""

from __future__ import annotations

from enum import StrEnum


class ExecutiveReportStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(StrEnum):
    MARKDOWN = "markdown"
    CSV = "csv"
    JSON = "json"
    PDF = "pdf"


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
