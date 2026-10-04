"""Production security headers with optional HSTS."""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Environment


class SecurityHeadersMiddleware:
    """Append security headers to every HTTP response."""

    def __init__(self, app: ASGIApp, *, environment: Environment) -> None:
        self._app = app
        self._environment = environment

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        extra_headers = self._headers_for_environment()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.extend(extra_headers)
            await send(message)

        await self._app(scope, receive, send_wrapper)

    def _headers_for_environment(self) -> tuple[tuple[bytes, bytes], ...]:
        headers: list[tuple[bytes, bytes]] = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"strict-origin-when-cross-origin"),
            (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
            (b"cross-origin-opener-policy", b"same-origin"),
            (b"cross-origin-resource-policy", b"same-origin"),
        ]
        if self._environment in {Environment.PRODUCTION, Environment.STAGING}:
            headers.append(
                (b"strict-transport-security", b"max-age=31536000; includeSubDomains")
            )
            headers.append(
                (
                    b"content-security-policy",
                    b"default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
                )
            )
        return tuple(headers)
