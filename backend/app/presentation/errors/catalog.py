"""Stable machine-readable error codes for API clients."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ErrorCodeDefinition:
    code: str
    http_status: int
    message: str
    description: str


ERROR_CATALOG: dict[str, ErrorCodeDefinition] = {
    "authentication_error": ErrorCodeDefinition(
        code="authentication_error",
        http_status=401,
        message="Authentication required or credentials invalid.",
        description="Missing/invalid JWT or refresh token.",
    ),
    "forbidden": ErrorCodeDefinition(
        code="forbidden",
        http_status=403,
        message="You do not have permission to perform this action.",
        description="RBAC denial — authenticated but insufficient role/permission.",
    ),
    "not_found": ErrorCodeDefinition(
        code="not_found",
        http_status=404,
        message="The requested resource was not found.",
        description="Resource missing or not visible in tenant scope.",
    ),
    "validation_error": ErrorCodeDefinition(
        code="validation_error",
        http_status=422,
        message="Request validation failed.",
        description="Pydantic/business validation failure.",
    ),
    "conflict": ErrorCodeDefinition(
        code="conflict",
        http_status=409,
        message="The request conflicts with current state.",
        description="Duplicate resource or state conflict.",
    ),
    "rate_limit_exceeded": ErrorCodeDefinition(
        code="rate_limit_exceeded",
        http_status=429,
        message="Too many requests. Please retry later.",
        description="SlowAPI or global throttle limit hit.",
    ),
    "payload_too_large": ErrorCodeDefinition(
        code="payload_too_large",
        http_status=413,
        message="Request body exceeds the maximum allowed size.",
        description="PayloadSizeLimitMiddleware rejection.",
    ),
    "unsupported_media_type": ErrorCodeDefinition(
        code="unsupported_media_type",
        http_status=415,
        message="Content-Type must be application/json.",
        description="ContentTypeValidationMiddleware rejection.",
    ),
    "service_unavailable": ErrorCodeDefinition(
        code="service_unavailable",
        http_status=503,
        message="A required service is temporarily unavailable.",
        description="Dependency failure, circuit open, or readiness degraded.",
    ),
    "circuit_open": ErrorCodeDefinition(
        code="circuit_open",
        http_status=503,
        message="Service temporarily unavailable due to repeated failures.",
        description="Circuit breaker is open.",
    ),
    "internal_error": ErrorCodeDefinition(
        code="internal_error",
        http_status=500,
        message="An unexpected error occurred.",
        description="Unhandled exception — no stack trace exposed.",
    ),
    "idempotency_conflict": ErrorCodeDefinition(
        code="idempotency_conflict",
        http_status=409,
        message="A request with this idempotency key is already in progress.",
        description="Duplicate Idempotency-Key while prior request processing.",
    ),
}
