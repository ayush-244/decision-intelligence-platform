"""API version 1.

All v1 endpoints are aggregated in ``router.py`` and mounted under the
``DELPHI_API_V1_PREFIX`` (default ``/api/v1``). Introducing a ``v2`` later means
adding a sibling package and mounting it in parallel — existing clients are
never broken.
"""

from app.presentation.api.v1.router import api_v1_router

__all__ = ["api_v1_router"]
