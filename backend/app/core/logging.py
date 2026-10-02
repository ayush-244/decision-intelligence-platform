"""Structured logging configuration.

Logging strategy
----------------
* **Structured, not string-formatted.** Every log line is a set of key/value
  pairs rendered either as JSON (production, for ingestion by Loki/Datadog/ELK)
  or as human-friendly coloured console output (local development). The choice
  is controlled by ``DELPHI_LOG_FORMAT``.
* **Context propagation via ``contextvars``.** A per-request ``request_id`` is
  bound once in middleware and automatically attached to every subsequent log
  line for that request — no need to thread the id through function signatures.
* **Single pipeline.** ``structlog`` is configured to also process records
  emitted by the standard library (uvicorn, SQLAlchemy), so the entire process
  produces one consistent log format.
* **Levels.** Standard library levels; the threshold is set from
  ``DELPHI_LOG_LEVEL``. Application code should prefer ``INFO`` for lifecycle
  events, ``WARNING`` for recoverable anomalies, and ``ERROR`` for failures.
* **Future file logging.** The pipeline writes to stdout only (the 12-factor
  approach — the runtime/orchestrator owns log routing). A rotating file
  handler can be added later without touching call sites; a hook is documented
  inline below.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import LogFormat, LogLevel, Settings

# Shared context for the current request (request_id, and future user/tenant).
# structlog reads/writes this contextvar transparently.
_shared_context = structlog.contextvars


def _drop_color_message_key(
    _logger: logging.Logger, _method_name: str, event_dict: EventDict
) -> EventDict:
    """Remove uvicorn's duplicate ``color_message`` key to keep logs clean."""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging(settings: Settings) -> None:
    """Configure structlog + stdlib logging for the whole process.

    Idempotent: safe to call once during application startup. Reconfiguring is
    harmless but unnecessary.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    # Processors shared by both structlog-native and stdlib log records.
    shared_processors: list[Processor] = [
        _shared_context.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _drop_color_message_key,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format is LogFormat.JSON:
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty())

    # structlog-native loggers: prepare records then hand off to stdlib.
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # A single formatter renders both structlog and plain-stdlib records.
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # NOTE (future file logging): add a RotatingFileHandler with the same
    # `formatter` here and attach it to `root` — no call sites need to change.

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(_to_stdlib_level(settings.log_level))

    # Align noisy third-party loggers with our pipeline.
    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(noisy).handlers.clear()
        logging.getLogger(noisy).propagate = True


def _to_stdlib_level(level: LogLevel) -> int:
    """Translate our ``LogLevel`` enum into a stdlib numeric level."""
    return logging.getLevelNamesMapping()[level.value]


def get_logger(name: str | None = None, **initial_values: Any) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger, optionally pre-bound with context."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    if initial_values:
        return logger.bind(**initial_values)
    return logger


def bind_request_context(**values: Any) -> None:
    """Bind key/value pairs (e.g. ``request_id``) to the current context."""
    _shared_context.bind_contextvars(**values)


def clear_request_context() -> None:
    """Clear all request-scoped context (call at the end of each request)."""
    _shared_context.clear_contextvars()
