
"""Unit tests for encryption key configuration."""

import base64
import os

import pytest

from leakguard.config.encryption import create_crypto_service_from_env


@pytest.fixture(autouse=True)
def isolate_encryption_environment(monkeypatch):
    monkeypatch.setattr(
        "leakguard.config.encryption.load_dotenv",
        lambda: None,
    )
    monkeypatch.delenv("LEAKGUARD_ENCRYPTION_KEY", raising=False)


def test_valid_encryption_key_configuration(monkeypatch):
    key = os.urandom(32)
    encoded_key = base64.b64encode(key).decode("ascii")

    monkeypatch.setenv("LEAKGUARD_ENCRYPTION_KEY", encoded_key)

    first = create_crypto_service_from_env()
    second = create_crypto_service_from_env()

    plaintext = "Confidential organizational information"
    encrypted = first.encrypt(plaintext)

    assert second.decrypt(encrypted) == plaintext


def test_missing_encryption_key_is_rejected():
    with pytest.raises(
        ValueError,
        match="LEAKGUARD_ENCRYPTION_KEY is not configured",
    ):
        create_crypto_service_from_env()


@pytest.mark.parametrize("encoded_key", [
    "invalid-base64!",
    "not a valid key",
])
def test_invalid_base64_key_is_rejected(monkeypatch, encoded_key):
    monkeypatch.setenv("LEAKGUARD_ENCRYPTION_KEY", encoded_key)

    with pytest.raises(ValueError, match="must be valid Base64"):
        create_crypto_service_from_env()


@pytest.mark.parametrize("key_length", [16, 31, 33])
def test_invalid_key_length_is_rejected(monkeypatch, key_length):
    key = os.urandom(key_length)
    encoded_key = base64.b64encode(key).decode("ascii")

    monkeypatch.setenv("LEAKGUARD_ENCRYPTION_KEY", encoded_key)

    with pytest.raises(ValueError, match="AES-256 requires a 32-byte key"):
        create_crypto_service_from_env()
