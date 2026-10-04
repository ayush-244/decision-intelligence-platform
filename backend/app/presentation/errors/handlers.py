"""Exception handlers producing the consistent error envelope.

Three tiers of handling:

1. :class:`DelphiError` — expected, semantic application errors. Mapped to the
   status code and code carried by the exception.
2. ``RequestValidationError`` — malformed input. Returned as ``422`` with the
   field-level details Pydantic produced.
3. ``Exception`` — anything unexpected. Logged with full context and returned as
   an opaque ``500`` so internal details never leak to clients.
"""

from __future__ import annotations

from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.presentation.errors.schemas import ErrorDetail, ErrorResponse
from app.shared.exceptions import DelphiError

_logger = get_logger(__name__)


def _request_id(request: Request) -> str | None:
    """Extract the correlation id attached by the request-context middleware."""
    scope_state = request.scope.get("state")
    if isinstance(scope_state, dict):
        scope_value = scope_state.get("request_id")
        if scope_value is not None:
            return str(scope_value)
    value = getattr(request.state, "request_id", None)
    return str(value) if value is not None else None


def _envelope(
    *,
    code: str,
    message: str,
    status_code: int,
    request: Request,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    """Build a JSONResponse wrapping the standard error envelope."""
    payload = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or {},
            request_id=_request_id(request),
        )
    )
    # Correlation id is echoed by RequestContextMiddleware; avoid duplicate headers.
    return JSONResponse(status_code=status_code, content=payload.model_dump())


async def _handle_delphi_error(request: Request, exc: DelphiError) -> JSONResponse:
    _logger.warning(
        "application_error",
        code=exc.code,
        status_code=exc.status_code,
        message=exc.message,
    )
    return _envelope(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request=request,
        details=exc.details,
    )


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _envelope(
        code="validation_error",
        message="Request validation failed.",
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        request=request,
        details={"errors": exc.errors()},
    )


async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _envelope(
        code=HTTPStatus(exc.status_code).name.lower(),
        message=str(exc.detail),
        status_code=exc.status_code,
        request=request,
    )


async def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    _logger.exception("unhandled_exception", error=str(exc))
    return _envelope(
        code="internal_error",
        message="An unexpected error occurred.",
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        request=request,
    )


async def _handle_rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    _logger.warning("rate_limit_exceeded", detail=str(exc.detail))
    return _envelope(
        code="rate_limit_exceeded",
        message="Too many requests. Please retry later.",
        status_code=HTTPStatus.TOO_MANY_REQUESTS,
        request=request,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application."""
    app.add_exception_handler(DelphiError, _handle_delphi_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(RateLimitExceeded, _handle_rate_limit_exceeded)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected_error)
