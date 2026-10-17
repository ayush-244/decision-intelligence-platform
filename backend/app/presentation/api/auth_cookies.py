"""Refresh-token cookie helpers for httpOnly session continuity."""

from __future__ import annotations

from fastapi import Response

from app.core.config import Settings


def set_refresh_token_cookie(
    response: Response,
    *,
    settings: Settings,
    refresh_token: str,
) -> None:
    """Attach the rotating refresh token as a secure httpOnly cookie."""
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.jwt_refresh_token_expire_days * 86_400,
        path=f"{settings.api_v1_prefix}/auth",
    )


def clear_refresh_token_cookie(response: Response, *, settings: Settings) -> None:
    """Remove the refresh token cookie on logout."""
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        path=f"{settings.api_v1_prefix}/auth",
    )
