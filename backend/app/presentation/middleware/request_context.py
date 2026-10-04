"""Correlation-id + access-logging middleware.

For every request this middleware:

* Reuses an inbound ``X-Request-ID`` header or mints a new UUID, so requests can
  be traced end-to-end across clients, proxies, and logs.
* Binds the id (plus method/path) into the structlog context so *every* log
  line emitted while handling the request carries it automatically.
* Emits a single structured access log with method, path, status, and duration.
* Echoes the id back in the response header and clears the log context.
"""

from __future__ import annotations

import re
import time
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.constants import REQUEST_ID_HEADER, REQUEST_ID_LOG_KEY, REQUEST_ID_MAX_LENGTH
from app.core.logging import bind_request_context, clear_request_context, get_logger

_logger = get_logger("http.access")
_HEADER_BYTES = REQUEST_ID_HEADER.lower().encode("latin-1")
_REQUEST_ID_PATTERN = re.compile(r"^[\w\-]{1,128}$")


class RequestContextMiddleware:
    """Pure-ASGI middleware for correlation ids and access logs.

    Implemented at the ASGI level (rather than ``BaseHTTPMiddleware``) to avoid
    the latter's known overhead and streaming edge-cases, and to reliably set
    the response header before the body is sent.
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        request_id = self._extract_or_create_id(scope)
        method = scope.get("method", "-")
        path = scope.get("path", "-")

        # Expose to handlers/exception handlers and to the logging context.
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id
        bind_request_context(**{REQUEST_ID_LOG_KEY: request_id, "method": method, "path": path})

        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = message.setdefault("headers", [])
                headers.append((_HEADER_BYTES, request_id.encode("latin-1")))
            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _logger.info(
                "request_completed",
                status_code=status_code,
                duration_ms=duration_ms,
            )
            clear_request_context()

    @staticmethod
    def _extract_or_create_id(scope: Scope) -> str:
        """Return a validated inbound request id or mint a fresh UUID4."""
        for name, value in scope.get("headers", []):
            if name == _HEADER_BYTES:
                decoded: str = value.decode("latin-1").strip()
                if decoded and RequestContextMiddleware._is_valid_request_id(decoded):
                    return decoded[:REQUEST_ID_MAX_LENGTH]
        return str(uuid4())

    @staticmethod
    def _is_valid_request_id(value: str) -> bool:
        """Reject oversized or malformed correlation ids (log injection / DoS)."""
        return (
            len(value) <= REQUEST_ID_MAX_LENGTH and _REQUEST_ID_PATTERN.fullmatch(value) is not None
        )
