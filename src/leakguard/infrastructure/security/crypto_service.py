"""CryptoService (ADD 5.2.11)."""

from __future__ import annotations


class CryptoService:
    """AES-256-GCM encryption of the fields marked *encrypted* (NFR-01).

    The key comes from the environment or a mounted key file (RL-07), never the database.
    """

    def __init__(self, key: bytes) -> None:
        """``key``: a 32-byte AES-256-GCM key."""
        self._key = key

    def encrypt(self, text: str) -> bytes:
        """Encrypt with a fresh random nonce each call, so encrypt(x) <> encrypt(x)."""
        raise NotImplementedError

    def decrypt(self, data: bytes) -> str:
        """Post: decrypt(encrypt(x)) = x. Altered data raises an error."""
        raise NotImplementedError
