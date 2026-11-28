"""End-to-end checks through the real LiteLLM proxy started from config/litellm.yaml, with the
real LeakGuard hook and the mock LLM recording what it receives (issues #9, #12):

    client (httpx) -> LiteLLM proxy -> LeakGuard hook -> mock LLM -> back to the client
"""

from __future__ import annotations

import httpx
import pytest

pytest.importorskip("litellm")

from leakguard.infrastructure.litellm.mock_llm_provider import (  # noqa: E402
    RECEIVED_EVENT,
    parse_echo,
    read_events,
)
from tests.utils.litellm_proxy import PROJECT_ROOT, start_proxy, stream_content  # noqa: E402

MARKER = "ORION-FICTIONAL-SECRET-7731"  # fictional text whose presence shows a leak
CHAT_REQUEST = {
    "model": "leakguard-mock",
    "messages": [{"role": "user", "content": "hello LeakGuard"}],
}
# The shape of a chat request from Open WebUI (assumed from the OpenAI format, not captured):
# streaming, a system prompt, multi-turn, content parts and sampling options.
OPEN_WEBUI_REQUEST = {
    "model": "leakguard-mock",
    "stream": True,
    "stream_options": {"include_usage": True},
    "temperature": 0.7,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": [{"type": "text", "text": "Please summarize the following document."}]},
        {"role": "assistant", "content": "Sure, please paste it."},
        {"role": "user", "content": "Quarterly planning notes for the team offsite."},
    ],
}


@pytest.fixture(scope="module")
def proxy(tmp_path_factory):
    with start_proxy(PROJECT_ROOT / "config" / "litellm.yaml", tmp_path_factory.mktemp("litellm")) as running:
        yield running


@pytest.fixture
def record(proxy):
    """The mock LLM's record file, emptied before the test."""
    return proxy.clear_record()


def _chat(proxy, body: dict, headers: dict | None = None) -> httpx.Response:
    return httpx.post(f"{proxy.base_url}/v1/chat/completions", json=body, headers=headers, timeout=30)


# 8
def test_request_without_master_key_never_reaches_the_mock_llm(proxy, record):
    body = {"model": "leakguard-mock", "messages": [{"role": "user", "content": f"unauthenticated {MARKER}"}]}

    response = _chat(proxy, body)

    # LiteLLM 1.108.20 answers 500 here (its auth error handler needs the optional `prisma`
    # package); what matters is that the request is rejected and never reaches the model.
    assert response.status_code >= 400
    assert read_events(record) == []
    assert MARKER not in response.text


def test_leakguard_guardrail_is_registered(proxy):
    response = httpx.get(f"{proxy.base_url}/guardrails/list", headers=proxy.auth, timeout=30)
    assert response.status_code == 200
    assert "leakguard" in [g["guardrail_name"] for g in response.json()["guardrails"]]


# 7
def test_approved_request_reaches_the_mock_llm_unchanged(proxy, record):
    response = _chat(proxy, CHAT_REQUEST, proxy.auth)

    assert response.status_code == 200
    assert parse_echo(response.json()["choices"][0]["message"]["content"]) == CHAT_REQUEST["messages"]
    assert read_events(record) == [
        {"event": RECEIVED_EVENT, "model": "echo", "messages": CHAT_REQUEST["messages"]}
    ]


# 9
def test_open_webui_style_streaming_request_reaches_the_mock_llm_unchanged(proxy, record):
    response = _chat(proxy, OPEN_WEBUI_REQUEST, proxy.auth)

    assert response.status_code == 200
    assert parse_echo(stream_content(response)) == OPEN_WEBUI_REQUEST["messages"]
    events = read_events(record)
    assert [event["event"] for event in events] == [RECEIVED_EVENT]
    assert events[0]["messages"] == OPEN_WEBUI_REQUEST["messages"]
