"""Application-wide constants.

Centralising magic strings/numbers here keeps them discoverable and prevents
duplication. Anything that would otherwise be a hardcoded literal in more than
one place belongs in this module.
"""

from __future__ import annotations

from typing import Final

# HTTP header carrying the correlation id across the request lifecycle.
REQUEST_ID_HEADER: Final[str] = "X-Request-ID"

# Distributed trace id (W3C traceparent or standalone header).
TRACE_ID_HEADER: Final[str] = "X-Trace-ID"
TRACE_ID_LOG_KEY: Final[str] = "trace_id"

# Idempotency key for safe mutation retries.
IDEMPOTENCY_KEY_HEADER: Final[str] = "Idempotency-Key"

# Key used for the request id in log context and error payloads.
REQUEST_ID_LOG_KEY: Final[str] = "request_id"

# Default timeout (seconds) for datastore health probes.
HEALTH_PROBE_TIMEOUT_SECONDS: Final[float] = 2.0

# Generic client-facing message when a health probe fails (never expose internals).
HEALTH_PROBE_FAILURE_DETAIL: Final[str] = "Dependency unavailable"

# Maximum length for inbound correlation IDs.
REQUEST_ID_MAX_LENGTH: Final[int] = 128
