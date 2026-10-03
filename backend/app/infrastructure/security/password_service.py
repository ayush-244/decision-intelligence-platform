"""Argon2 password hashing."""

from __future__ import annotations

import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_HASHER = PasswordHasher()
_PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,128}$")


class PasswordService:
    """Hash and verify passwords using Argon2id."""

    def validate(self, password: str) -> None:
        if not _PASSWORD_PATTERN.match(password):
            msg = "Password must be 8-128 characters and include at least one letter and one digit."
            raise ValueError(msg)

    def hash(self, password: str) -> str:
        self.validate(password)
        return _HASHER.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return _HASHER.verify(password_hash, password)
        except VerifyMismatchError:
            return False
