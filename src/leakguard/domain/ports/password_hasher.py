"""«interface» PasswordHasher."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """Hashes and checks passwords (NFR-06)."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a salted hash. Post: result <> password."""

    @abstractmethod
    def verify(self, password: str, hash: str) -> bool:
        """Return True if the password matches the hash."""
