"""CryptoService (ADD 5.2.11)."""

from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoService:
    """AES-256-GCM encryption of the fields marked *encrypted* (NFR-01).

    The key comes from the environment or a mounted key file (RL-07), never the database.
    """
    NONCE_SIZE = 12

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("AES-256 requires a 32-byte key")
        self._key = key

    def encrypt(self, text: str) -> bytes:
        """Encrypt with a fresh random nonce each call, so encrypt(x) <> encrypt(x)."""
        nonce = os.urandom(self.NONCE_SIZE)
        plaintext = text.encode("utf-8")

        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return nonce + ciphertext

    def decrypt(self, data: bytes) -> str:
        """Post: decrypt(encrypt(x)) = x. Altered data raises an error."""
        if not isinstance(data, bytes):
            raise TypeError("Encrypted data must be bytes")

        if len(data) < self.NONCE_SIZE + 16:
            raise ValueError("Invalid encrypted data length")

        nonce = data[:self.NONCE_SIZE]
        ciphertext = data[self.NONCE_SIZE:]

        aesgcm = AESGCM(self._key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode("utf-8")
