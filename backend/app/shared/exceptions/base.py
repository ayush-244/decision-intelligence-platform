"""Base exception types for the application.

Design
------
Inner layers (domain/application) raise semantic errors that describe *what*
went wrong in business terms, not *how* it should be presented. Each error
carries a stable, machine-readable ``code`` and a default HTTP status. The
presentation layer maps these to a consistent JSON envelope, so adding a new
failure mode never requires touching HTTP wiring.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any


class DelphiError(Exception):
    """Base class for all expected, handled application errors.

    Attributes:
        message: Human-readable description safe to surface to API clients.
        code: Stable machine-readable identifier (e.g. ``"not_found"``).
        status_code: HTTP status the presentation layer should return.
        details: Optional structured context (never include secrets).
    """

    code: str = "internal_error"
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}


class BusinessValidationError(DelphiError):
    """Input failed a business/validation rule."""

    code = "validation_error"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class NotFoundError(DelphiError):
    """A requested resource does not exist."""

    code = "not_found"
    status_code = HTTPStatus.NOT_FOUND


class ConflictError(DelphiError):
    """The request conflicts with the current state of a resource."""

    code = "conflict"
    status_code = HTTPStatus.CONFLICT


class ServiceUnavailableError(DelphiError):
    """A required downstream dependency is unavailable."""

    code = "service_unavailable"
    status_code = HTTPStatus.SERVICE_UNAVAILABLE


class AuthenticationError(DelphiError):
    """Authentication failed or credentials are invalid."""

    code = "authentication_error"
    status_code = HTTPStatus.UNAUTHORIZED


class ForbiddenError(DelphiError):
    """The caller is authenticated but lacks permission."""

    code = "forbidden"
    status_code = HTTPStatus.FORBIDDEN
