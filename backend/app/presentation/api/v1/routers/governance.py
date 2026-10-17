"""API governance endpoints — error catalog and versioning policy."""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.schemas.common import DataResponse
from app.presentation.errors.catalog import ERROR_CATALOG

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get(
    "/errors",
    response_model=DataResponse[list[dict]],
    summary="Machine-readable API error catalog",
)
async def error_catalog() -> DataResponse[list[dict]]:
    """Return stable error codes for client integration and compliance documentation."""
    entries = [
        {
            "code": item.code,
            "http_status": item.http_status,
            "message": item.message,
            "description": item.description,
        }
        for item in ERROR_CATALOG.values()
    ]
    return DataResponse(data=entries)


@router.get(
    "/versioning",
    response_model=DataResponse[dict],
    summary="API versioning and deprecation policy",
)
async def versioning_policy() -> DataResponse[dict]:
    return DataResponse(
        data={
            "current_version": "v1",
            "prefix": "/api/v1",
            "deprecation_policy": "Breaking changes require a new major version path.",
            "sunset_notice_days": 90,
            "idempotency_header": "Idempotency-Key",
            "correlation_headers": ["X-Request-ID", "X-Trace-ID"],
        }
    )
