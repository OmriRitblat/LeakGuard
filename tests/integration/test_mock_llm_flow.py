"""The LeakGuard hook receives exactly what the client sent; the prompt reaches the mock LLM
only after the hook approves it, and only as the hook returns it (issue #12; UC-02, FR-02,
FR-09, FR-10, NFR-04).

Uses tests/utils/litellm_test.yaml: test doubles of the LeakGuard hook stand in for the
decisions the inspection pipeline will make, and each request chooses one with
"guardrails": ["<name>"]. The hook doubles and the mock LLM write to one record file, so its
lines show what happened and in which order.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

pytest.importorskip("litellm")

from leakguard.infrastructure.litellm.mock_llm_provider import (  # noqa: E402
    RECEIVED_EVENT,
    parse_echo,
    read_events,
)
from tests.utils.litellm_doubles import (  # noqa: E402
    HOOK_APPROVED,
    HOOK_REJECTED,
    HOOK_REPLACED,
    REPLACEMENT_MESSAGES,
)
from tests.utils.litellm_proxy import start_proxy, stream_content  # noqa: E402

TEST_CONFIG = Path(__file__).resolve().parents[1] / "utils" / "litellm_test.yaml"
MARKER = "ORION-FICTIONAL-SECRET-7731"  # fictional text whose presence shows a leak
# An Open WebUI-style request (assumed shape, not captured), with a user identifier (UC-02 input).
CLIENT_REQUEST = {
    "model": "leakguard-mock",
    "temperature": 0.7,
    "user": "fictional-user-42",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [{"type": "text", "text": "Please summarize the following document."}]},
        {"role": "assistant", "content": "Sure, please paste it."},
        {"role": "user", "content": "Quarterly planning notes for the team offsite."},
    ],
}
PROMPT_MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": f"Summarize the launch plan of {MARKER}."},
]


@pytest.fixture(scope="module")
def proxy(tmp_path_factory):
    with start_proxy(TEST_CONFIG, tmp_path_factory.mktemp("litellm_doubles")) as running:
        yield running


@pytest.fixture
def record(proxy):
    """The record file shared by the hook doubles and the mock LLM, emptied before the test."""
    return proxy.clear_record()


def _chat(proxy, guardrail: str, *, stream: bool = False, body: dict | None = None) -> httpx.Response:
    body = {"model": "leakguard-mock", "messages": PROMPT_MESSAGES, "stream": stream, **(body or {}),
            "guardrails": [guardrail]}
    return httpx.post(f"{proxy.base_url}/v1/chat/completions", json=body, headers=proxy.auth, timeout=30)


def _answer(response: httpx.Response, stream: bool) -> str:
    return stream_content(response) if stream else response.json()["choices"][0]["message"]["content"]


# 13
@pytest.mark.parametrize("stream", [False, True], ids=["normal", "stream"])
def test_leakguard_hook_receives_exactly_what_the_client_sent(proxy, record, stream):
    response = _chat(proxy, "spy", stream=stream, body=CLIENT_REQUEST)

    assert response.status_code == 200
    hook_event = read_events(record)[0]
    assert hook_event == {
        "event": HOOK_APPROVED,
        "call_type": "acompletion",
        "model": CLIENT_REQUEST["model"],
        "messages": CLIENT_REQUEST["messages"],
        "stream": stream,
        "temperature": CLIENT_REQUEST["temperature"],
        "user": CLIENT_REQUEST["user"],
    }


# 10
@pytest.mark.parametrize("stream", [False, True], ids=["normal", "stream"])
def test_mock_llm_is_called_only_after_the_hook_approves(proxy, record, stream):
    response = _chat(proxy, "spy", stream=stream)

    assert response.status_code == 200
    events = read_events(record)
    assert [event["event"] for event in events] == [HOOK_APPROVED, RECEIVED_EVENT]
    assert events[0]["messages"] == PROMPT_MESSAGES
    assert events[1]["messages"] == PROMPT_MESSAGES
    assert parse_echo(_answer(response, stream)) == PROMPT_MESSAGES


# 11
@pytest.mark.parametrize("stream", [False, True], ids=["normal", "stream"])
def test_rejected_prompt_never_reaches_the_mock_llm(proxy, record, stream):
    response = _chat(proxy, "reject", stream=stream)

    assert response.status_code >= 400
    assert [event["event"] for event in read_events(record)] == [HOOK_REJECTED]
    assert MARKER not in record.read_text(encoding="utf-8")
    assert MARKER not in response.text


# 12
@pytest.mark.parametrize("stream", [False, True], ids=["normal", "stream"])
def test_only_the_messages_the_hook_returns_reach_the_mock_llm(proxy, record, stream):
    response = _chat(proxy, "replace", stream=stream)

    assert response.status_code == 200
    assert parse_echo(_answer(response, stream)) == REPLACEMENT_MESSAGES
    events = read_events(record)
    assert [event["event"] for event in events] == [HOOK_REPLACED, RECEIVED_EVENT]
    assert events[1]["messages"] == REPLACEMENT_MESSAGES
    assert MARKER not in record.read_text(encoding="utf-8")
    assert MARKER not in response.text
