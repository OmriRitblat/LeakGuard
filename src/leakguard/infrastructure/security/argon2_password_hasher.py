"""Argon2PasswordHasher."""

from __future__ import annotations

from leakguard.domain.ports.password_hasher import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """PasswordHasher with Argon2 (argon2-cffi), NFR-06."""

    def hash(self, password: str) -> str:
        raise NotImplementedError

    def verify(self, password: str, hash: str) -> bool:
        raise NotImplementedError
