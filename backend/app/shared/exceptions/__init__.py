"""Application exception hierarchy.

All domain/application errors derive from :class:`DelphiError`, giving the
presentation layer a single, structured way to translate failures into HTTP
responses (see ``app.presentation.errors``). Raising these instead of ad-hoc
``HTTPException`` keeps inner layers framework-agnostic.
"""

from app.shared.exceptions.base import (
    AuthenticationError,
    BusinessValidationError,
    ConflictError,
    DelphiError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
)

__all__ = [
    "AuthenticationError",
    "BusinessValidationError",
    "ConflictError",
    "DelphiError",
    "ForbiddenError",
    "NotFoundError",
    "ServiceUnavailableError",
]
