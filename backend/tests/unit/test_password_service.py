"""Password hashing unit tests."""

from __future__ import annotations

import pytest

from app.infrastructure.security.password_service import PasswordService

pytestmark = pytest.mark.unit


def test_hash_and_verify_round_trip() -> None:
    service = PasswordService()
    password_hash = service.hash("Password1")
    assert service.verify("Password1", password_hash)
    assert not service.verify("WrongPassword1", password_hash)


def test_validate_rejects_weak_password() -> None:
    service = PasswordService()
    with pytest.raises(ValueError, match="Password must"):
        service.validate("abc")
