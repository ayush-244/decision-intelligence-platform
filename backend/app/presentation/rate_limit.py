"""Shared SlowAPI limiter instance."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Default global limit — overridden per-route for auth; tests patch settings.
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

