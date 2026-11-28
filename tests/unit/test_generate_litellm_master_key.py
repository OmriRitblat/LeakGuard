"""Unit tests for local LiteLLM master key generation."""

import re

import pytest
from dotenv import dotenv_values

from scripts import generate_litellm_master_key

KEY_PATTERN = re.compile(r"sk-[0-9a-f]{64}")


@pytest.fixture
def env_path(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    monkeypatch.setattr(generate_litellm_master_key, "ENV_PATH", path)
    return path


def test_generates_master_key(env_path):
    env_path.write_text("POSTGRES_DB=leakguard\n")

    generate_litellm_master_key.main()

    assert KEY_PATTERN.fullmatch(dotenv_values(env_path)["LITELLM_MASTER_KEY"])


def test_populates_empty_master_key(env_path):
    env_path.write_text("LITELLM_MASTER_KEY=\n")

    generate_litellm_master_key.main()

    assert KEY_PATTERN.fullmatch(dotenv_values(env_path)["LITELLM_MASTER_KEY"])


def test_does_not_replace_existing_master_key(env_path):
    env_path.write_text("LITELLM_MASTER_KEY=sk-existing\n")

    generate_litellm_master_key.main()

    assert dotenv_values(env_path)["LITELLM_MASTER_KEY"] == "sk-existing"


def test_repeated_execution_preserves_master_key(env_path):
    env_path.write_text("POSTGRES_DB=leakguard\n")

    generate_litellm_master_key.main()
    first_key = dotenv_values(env_path)["LITELLM_MASTER_KEY"]
    generate_litellm_master_key.main()

    assert dotenv_values(env_path)["LITELLM_MASTER_KEY"] == first_key


def test_missing_env_file_stops_with_message(env_path):
    with pytest.raises(SystemExit, match="Copy .env.example to .env"):
        generate_litellm_master_key.main()
