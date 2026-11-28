"""Tests for the mock_llm section of the LeakGuard settings (issue #12)."""

from __future__ import annotations

from leakguard.config.settings import load_settings

RECORD_FILE_ENV = "LEAKGUARD_MOCK_LLM__RECORD_FILE"


# 5
def test_mock_llm_recording_is_off_in_the_default_config(monkeypatch):
    monkeypatch.delenv("LEAKGUARD_CONFIG_FILE", raising=False)
    monkeypatch.delenv(RECORD_FILE_ENV, raising=False)

    assert load_settings().mock_llm.record_file is None


# 5
def test_mock_llm_record_file_can_be_set_from_the_environment(monkeypatch, tmp_path):
    record_file = tmp_path / "record.jsonl"
    monkeypatch.delenv("LEAKGUARD_CONFIG_FILE", raising=False)
    monkeypatch.setenv(RECORD_FILE_ENV, str(record_file))

    assert load_settings().mock_llm.record_file == record_file
