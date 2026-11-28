"""Unit tests for MockLLMProvider and its record/echo helpers (issue #12).

The provider is called directly: no proxy, no network.
"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("litellm")

from leakguard.infrastructure.litellm.mock_llm_provider import (  # noqa: E402
    RECEIVED_EVENT,
    MockLLMProvider,
    echo_content,
    mock_llm_provider,
    parse_echo,
    read_events,
    record_event,
)

# System prompt, multi-turn and content parts, as a chat client such as Open WebUI sends.
MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": [{"type": "text", "text": "Hello, please summarize this"}]},
    {"role": "assistant", "content": "Sure."},
    {"role": "user", "content": "Thanks"},
]


def _complete(provider: MockLLMProvider, messages: list) -> str:
    response = asyncio.run(provider.acompletion(model="echo", messages=messages))
    return response.choices[0].message.content


def _stream(provider: MockLLMProvider, messages: list) -> list:
    async def collect() -> list:
        return [chunk async for chunk in provider.astreaming(model="echo", messages=messages)]

    return asyncio.run(collect())


# 1
def test_acompletion_echoes_and_records_the_messages(tmp_path):
    record_file = tmp_path / "record.jsonl"

    content = _complete(MockLLMProvider(record_file=record_file), MESSAGES)

    assert parse_echo(content) == MESSAGES
    assert read_events(record_file) == [{"event": RECEIVED_EVENT, "model": "echo", "messages": MESSAGES}]


# 2
def test_astreaming_echoes_in_one_chunk_and_records_the_messages(tmp_path):
    record_file = tmp_path / "record.jsonl"

    chunks = _stream(MockLLMProvider(record_file=record_file), MESSAGES)

    assert len(chunks) == 1
    assert chunks[0]["is_finished"] is True
    assert chunks[0]["finish_reason"] == "stop"
    assert parse_echo(chunks[0]["text"]) == MESSAGES
    assert read_events(record_file) == [{"event": RECEIVED_EVENT, "model": "echo", "messages": MESSAGES}]


# 3
def test_recording_off_writes_no_file_and_still_echoes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # any file the provider wrote with a relative path would land here
    provider = MockLLMProvider(record_file=None)

    content = _complete(provider, MESSAGES)
    chunks = _stream(provider, MESSAGES)

    assert parse_echo(content) == MESSAGES
    assert parse_echo(chunks[0]["text"]) == MESSAGES
    assert list(tmp_path.iterdir()) == []


# 4
def test_echo_round_trip_keeps_the_messages():
    assert parse_echo(echo_content(MESSAGES)) == MESSAGES


# 4
def test_read_events_returns_the_lines_in_write_order(tmp_path):
    record_file = tmp_path / "record.jsonl"
    assert read_events(record_file) == []

    for number in range(3):
        record_event(record_file, {"event": "test", "number": number})

    assert [event["number"] for event in read_events(record_file)] == [0, 1, 2]


# 5
def test_module_provides_the_instance_litellm_calls():
    assert isinstance(mock_llm_provider, MockLLMProvider)
