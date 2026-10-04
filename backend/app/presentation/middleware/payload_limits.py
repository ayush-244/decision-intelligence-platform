"""Reject oversized request bodies before handlers execute."""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.constants import REQUEST_ID_HEADER


class PayloadSizeLimitMiddleware:
    """Enforce maximum Content-Length for mutating HTTP methods."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        if method in {"GET", "HEAD", "OPTIONS", "DELETE"}:
            await self._app(scope, receive, send)
            return

        content_length = self._content_length(scope)
        if content_length is not None and content_length > self._max_bytes:
            await self._reject(scope, send)
            return

        await self._app(scope, receive, send)

    @staticmethod
    def _content_length(scope: Scope) -> int | None:
        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    return int(value.decode("latin-1"))
                except ValueError:
                    return None
        return None

    async def _reject(self, scope: Scope, send: Send) -> None:
        request_id = scope.get("state", {}).get("request_id", "")
        body = json.dumps(
            {
                "error": {
                    "code": "payload_too_large",
                    "message": "Request body exceeds the maximum allowed size.",
                    "details": {},
                    "request_id": request_id or None,
                }
            }
        ).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("latin-1")),
        ]
        if request_id:
            headers.append((REQUEST_ID_HEADER.lower().encode("latin-1"), request_id.encode("latin-1")))
        await send({"type": "http.response.start", "status": 413, "headers": headers})
        await send({"type": "http.response.body", "body": body})
