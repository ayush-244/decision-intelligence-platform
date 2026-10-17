"""Performance profiling — OpenTelemetry-compatible timing foundation."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.application.services.infrastructure.metrics_service import MetricsCollector


class PerformanceProfiler:
    """Record operation durations and flag slow queries."""

    def __init__(self, collector: MetricsCollector) -> None:
        self._collector = collector

    def profile(self, operation: str) -> "_ProfileBlock":
        return _ProfileBlock(self._collector, operation)


class _ProfileBlock:
    def __init__(self, collector: MetricsCollector, operation: str) -> None:
        self._collector = collector
        self._operation = operation
        self._start = perf_counter()

    def __enter__(self) -> _ProfileBlock:
        return self

    def __exit__(self, *args: Any) -> None:
        elapsed_ms = (perf_counter() - self._start) * 1000
        self._collector.record_duration(name=self._operation, duration_ms=elapsed_ms)
