
import os

import pytest
from cryptography.exceptions import InvalidTag

from leakguard.infrastructure.security.crypto_service import CryptoService


@pytest.fixture
def crypto():
    return CryptoService(os.urandom(32))


@pytest.mark.parametrize("text", [
    "Confidential organizational information",
    "",
    "Restricted internal financial records",
    "Confidential data " * 1000,
])
def test_encrypt_decrypt_roundtrip(crypto, text):
    encrypted = crypto.encrypt(text)

    assert isinstance(encrypted, bytes)
    assert crypto.decrypt(encrypted) == text


def test_same_plaintext_produces_different_ciphertexts(crypto):
    plaintext = "Internal financial report"

    first = crypto.encrypt(plaintext)
    second = crypto.encrypt(plaintext)

    assert first != second
    assert crypto.decrypt(first) == plaintext
    assert crypto.decrypt(second) == plaintext


def test_tampered_ciphertext_is_rejected(crypto):
    encrypted = bytearray(crypto.encrypt("Restricted business information"))
    encrypted[-1] ^= 1

    with pytest.raises(InvalidTag):
        crypto.decrypt(bytes(encrypted))


def test_tampered_nonce_is_rejected(crypto):
    encrypted = bytearray(crypto.encrypt("Restricted business information"))
    encrypted[0] ^= 1

    with pytest.raises(InvalidTag):
        crypto.decrypt(bytes(encrypted))


def test_decryption_with_wrong_key_is_rejected():
    first = CryptoService(os.urandom(32))
    second = CryptoService(os.urandom(32))

    encrypted = first.encrypt("Confidential business information")

    with pytest.raises(InvalidTag):
        second.decrypt(encrypted)


@pytest.mark.parametrize("key", [
    b"",
    b"short",
    os.urandom(16),
    os.urandom(31),
    os.urandom(33),
    "invalid key type",
])
def test_invalid_encryption_key_is_rejected(key):
    with pytest.raises(ValueError):
        CryptoService(key)


@pytest.mark.parametrize("data", [
    b"",
    b"invalid",
    bytes(27),
])
def test_invalid_encrypted_data_length_is_rejected(crypto, data):
    with pytest.raises(ValueError):
        crypto.decrypt(data)


def test_invalid_encrypted_data_type_is_rejected(crypto):
    with pytest.raises(TypeError):
        crypto.decrypt("invalid encrypted data")
