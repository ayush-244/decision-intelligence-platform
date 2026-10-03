"""JWT access token creation and verification."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from app.core.config import Settings
from app.shared.exceptions import AuthenticationError


class JwtService:
    """Creates and validates short-lived access tokens."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_access_token(self, *, user_id: UUID, email: str) -> tuple[str, int]:
        expires_delta = timedelta(minutes=self._settings.jwt_access_token_expire_minutes)
        expires_at = datetime.now(UTC) + expires_delta
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "email": email,
            "type": "access",
            "exp": expires_at,
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )
        return token, int(expires_delta.total_seconds())

    def decode_access_token(self, token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired access token.") from exc
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type.")
        return payload
