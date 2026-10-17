"""Presentation layer — the HTTP delivery mechanism (FastAPI).

The outermost layer. It translates HTTP requests into application use-case
calls and maps results/errors back into HTTP responses. It owns routers,
middleware, request/response schemas, exception handlers, and the dependency
wiring (composition root) — but contains **no** business logic itself.
"""
