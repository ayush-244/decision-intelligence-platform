"""Timezone-aware datetime helpers.

Always work in UTC internally; convert to local time only at presentation
boundaries. Centralising ``utc_now`` also makes time trivially mockable in
tests.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)
