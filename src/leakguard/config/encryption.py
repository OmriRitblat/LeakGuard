
"""Encryption key configuration."""

import base64
import binascii
import os

from dotenv import load_dotenv

from leakguard.infrastructure.security.crypto_service import CryptoService


def create_crypto_service_from_env() -> CryptoService:
    """Create a CryptoService using the configured encryption key."""
    load_dotenv()

    encoded_key = os.getenv("LEAKGUARD_ENCRYPTION_KEY")

    if not encoded_key:
        raise ValueError("LEAKGUARD_ENCRYPTION_KEY is not configured")

    try:
        key = base64.b64decode(encoded_key, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            "LEAKGUARD_ENCRYPTION_KEY must be valid Base64"
        ) from exc

    return CryptoService(key)
