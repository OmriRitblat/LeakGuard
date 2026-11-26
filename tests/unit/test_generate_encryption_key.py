
"""Unit tests for local encryption key generation."""

import base64

import pytest
from dotenv import dotenv_values

from scripts import generate_encryption_key


@pytest.fixture
def env_path(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    monkeypatch.setattr(generate_encryption_key, "ENV_PATH", path)
    return path


def test_generates_valid_encryption_key(env_path):
    env_path.write_text("POSTGRES_DB=leakguard\n")

    generate_encryption_key.main()

    encoded_key = dotenv_values(env_path)["LEAKGUARD_ENCRYPTION_KEY"]
    key = base64.b64decode(encoded_key, validate=True)

    assert len(key) == 32


def test_populates_empty_encryption_key(env_path):
    env_path.write_text("LEAKGUARD_ENCRYPTION_KEY=\n")

    generate_encryption_key.main()

    encoded_key = dotenv_values(env_path)["LEAKGUARD_ENCRYPTION_KEY"]

    assert len(base64.b64decode(encoded_key, validate=True)) == 32


def test_does_not_replace_existing_encryption_key(env_path):
    existing_key = base64.b64encode(bytes(range(32))).decode("ascii")
    env_path.write_text(
        f"LEAKGUARD_ENCRYPTION_KEY={existing_key}\n"
    )

    generate_encryption_key.main()

    assert dotenv_values(env_path)["LEAKGUARD_ENCRYPTION_KEY"] == existing_key


def test_repeated_execution_preserves_key(env_path):
    env_path.write_text("POSTGRES_DB=leakguard\n")

    generate_encryption_key.main()
    first_key = dotenv_values(env_path)["LEAKGUARD_ENCRYPTION_KEY"]

    generate_encryption_key.main()
    second_key = dotenv_values(env_path)["LEAKGUARD_ENCRYPTION_KEY"]

    assert first_key == second_key


def test_preserves_database_configuration(env_path):
    env_path.write_text(
        "POSTGRES_DB=leakguard\n"
        "POSTGRES_USER=leakguard\n"
        "POSTGRES_PORT=55432\n"
    )

    generate_encryption_key.main()

    config = dotenv_values(env_path)

    assert config["POSTGRES_DB"] == "leakguard"
    assert config["POSTGRES_USER"] == "leakguard"
    assert config["POSTGRES_PORT"] == "55432"
    assert config["LEAKGUARD_ENCRYPTION_KEY"]


def test_missing_env_file_is_rejected(env_path):
    with pytest.raises(SystemExit, match=".env file not found"):
        generate_encryption_key.main()

    assert not env_path.exists()


def test_encryption_key_is_not_printed(env_path, capsys):
    env_path.write_text("POSTGRES_DB=leakguard\n")

    generate_encryption_key.main()

    encoded_key = dotenv_values(env_path)["LEAKGUARD_ENCRYPTION_KEY"]
    output = capsys.readouterr()

    assert encoded_key not in output.out
    assert encoded_key not in output.err
