"""Lifecycle statuses for uploads, validation, and dataset versions."""

from __future__ import annotations

from enum import StrEnum


class UploadJobStatus(StrEnum):
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
