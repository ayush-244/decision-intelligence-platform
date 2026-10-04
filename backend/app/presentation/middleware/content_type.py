"""Validate Content-Type for JSON mutation endpoints."""

from __future__ import annotations

import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.constants import REQUEST_ID_HEADER

_JSON_METHODS = frozenset({"POST", "PUT", "PATCH"})
_SKIP_PATHS = frozenset({"/docs", "/redoc", "/openapi.json", "/health"})


class ContentTypeValidationMiddleware:
    """Require application/json for mutating API requests (except uploads)."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        method = scope.get("method", "GET")
        path = scope.get("path", "")
        if method not in _JSON_METHODS or self._should_skip(path):
            await self._app(scope, receive, send)
            return

        content_type = self._header(scope, b"content-type")
        if content_type and not content_type.startswith("application/json"):
            if "multipart/form-data" in content_type:
                await self._app(scope, receive, send)
                return
            await self._reject(scope, send, "unsupported_media_type", "Content-Type must be application/json.")
            return

        await self._app(scope, receive, send)

    @staticmethod
    def _should_skip(path: str) -> bool:
        if path in _SKIP_PATHS:
            return True
        return "/upload" in path

    @staticmethod
    def _header(scope: Scope, name: bytes) -> str | None:
        for header_name, value in scope.get("headers", []):
            if header_name == name:
                return value.decode("latin-1").lower()
        return None

    async def _reject(self, scope: Scope, send: Send, code: str, message: str) -> None:
        request_id = scope.get("state", {}).get("request_id", "")
        body = json.dumps(
            {
                "error": {
                    "code": code,
                    "message": message,
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
        await send({"type": "http.response.start", "status": 415, "headers": headers})
        await send({"type": "http.response.body", "body": body})
