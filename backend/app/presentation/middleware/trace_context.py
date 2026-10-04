"""W3C trace context propagation foundation."""

from __future__ import annotations

import re
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.constants import TRACE_ID_HEADER, TRACE_ID_LOG_KEY
from app.core.logging import bind_request_context

_TRACEPARENT_PATTERN = re.compile(
    r"^00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$",
    re.IGNORECASE,
)


class TraceContextMiddleware:
    """Parse traceparent or mint trace_id for distributed tracing readiness."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        trace_id = self._extract_trace_id(scope)
        scope.setdefault("state", {})
        scope["state"]["trace_id"] = trace_id
        bind_request_context(**{TRACE_ID_LOG_KEY: trace_id})

        trace_header = trace_id.encode("latin-1")
        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((TRACE_ID_HEADER.lower().encode("latin-1"), trace_header))
            await send(message)

        await self._app(scope, receive, send_wrapper)

    @staticmethod
    def _extract_trace_id(scope: Scope) -> str:
        for name, value in scope.get("headers", []):
            if name == b"traceparent":
                decoded = value.decode("latin-1").strip()
                if _TRACEPARENT_PATTERN.fullmatch(decoded):
                    return decoded.split("-")[1]
            if name == TRACE_ID_HEADER.lower().encode("latin-1"):
                candidate = value.decode("latin-1").strip()
                if candidate:
                    return candidate[:128]
        return uuid4().hex
