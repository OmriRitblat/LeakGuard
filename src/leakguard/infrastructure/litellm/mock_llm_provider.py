"""«POC test provider» MockLLMProvider: the controlled test provider of POC Stage 1 (ARD 5.3).

LiteLLM sends a request here, instead of to a real LLM provider, only after the LeakGuard
pre-call hook has approved it. The provider calls no external service: it answers with the
messages it received, so a client sees exactly what would have reached the LLM, and it can
record every received request to a JSON Lines file for tests (FR-09, FR-10, NFR-04).

Flow:
  At start-up, LiteLLM imports this module through ``custom_handler`` in config/litellm.yaml;
  the last line builds ``mock_llm_provider`` from ``mock_llm.record_file`` in
  config/leakguard.yaml (null = recording off).
  On every request the hook approved, LiteLLM calls ``acompletion`` (normal request) or
  ``astreaming`` (``stream: true``, as Open WebUI sends). Both record the request when
  recording is on, then answer with ``echo_content(messages)``. A request the hook rejected
  never reaches this module.
  Tests read the record with ``read_events`` and the answer with ``parse_echo``.

Registered in config/litellm.yaml:

    litellm_settings:
      custom_provider_map:
        - provider: leakguard-mock
          custom_handler: leakguard.infrastructure.litellm.mock_llm_provider.mock_llm_provider
"""

from __future__ import annotations

import json
import threading
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import litellm
from litellm import CustomLLM
from litellm.types.utils import GenericStreamingChunk

from leakguard.config.settings import load_settings

RECEIVED_EVENT = "mock_llm_received"

# Keeps each recorded line whole if two writers ever write at the same time. Today every write
# comes from LiteLLM's event-loop thread with no ``await`` between opening the file and writing
# the line, so writes cannot overlap and the lock is never contended. It protects the record if a
# caller writes from several threads (e.g. a synchronous completion run in a worker thread).
# It does not protect writers in different processes (e.g. several proxy workers).
_record_lock = threading.Lock()


def record_event(record_file: Path, event: dict[str, Any]) -> None:
    """Append ``event`` to ``record_file`` as one JSON line; the file is created if missing.

    The test hook doubles write to the same file, so hook and provider events share one order.
    """
    line = json.dumps(event, ensure_ascii=False)
    with _record_lock, record_file.open(mode="a", encoding="utf-8") as file:  # append: keep earlier lines
        file.write(line + "\n")


def read_events(record_file: Path) -> list[dict[str, Any]]:
    """Return the events of ``record_file`` in the order they were written ([] if it is missing)."""
    if not record_file.exists():
        return []
    with record_file.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def echo_content(messages: list[dict[str, Any]]) -> str:
    """The answer text: the received messages as JSON, ``{"received_messages": [...]}``.

    ``ensure_ascii=False`` keeps non-ASCII text (e.g. Hebrew) readable in the answer.
    """
    return json.dumps({"received_messages": messages}, ensure_ascii=False)


def parse_echo(content: str) -> list[dict[str, Any]]:
    """Inverse of echo_content: the messages the mock LLM received, read from its answer."""
    return json.loads(content)["received_messages"]


class MockLLMProvider(CustomLLM):
    """A LiteLLM custom provider that echoes, and optionally records, what it receives.

    Post Echo:   the answer content is echo_content(messages); with stream = true it is
                 streamed as one chunk.
    Post Record: record_file <> None implies one RECEIVED_EVENT line with the model and the
                 messages is appended before the answer is returned.
    Post NoCall: no network call is made, so no provider API key is needed.
    """

    def __init__(self, record_file: Path | None) -> None:
        super().__init__()
        self._record_file = record_file

    @classmethod
    def from_settings(cls) -> MockLLMProvider:
        """Build the provider from the ``mock_llm`` section of config/leakguard.yaml."""
        return cls(record_file=load_settings().mock_llm.record_file)

    async def acompletion(self, model: str, messages: list, *args: Any, **kwargs: Any) -> litellm.ModelResponse:
        """Normal request: record it, then return the whole echo as one answer."""
        self._receive(model, messages)
        return litellm.ModelResponse(
            model=model,
            choices=[{
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": echo_content(messages)},
            }],
        )

    async def astreaming(
        self, model: str, messages: list, *args: Any, **kwargs: Any
    ) -> AsyncIterator[GenericStreamingChunk]:
        """Streaming request (stream = true, as Open WebUI sends it): record it, then send the
        echo as a single stream piece; LiteLLM turns it into the ``data:`` lines of the answer."""
        self._receive(model, messages)
        yield GenericStreamingChunk(
            text=echo_content(messages),
            is_finished=True,
            finish_reason="stop",
            usage=None,
            index=0,
            tool_use=None,
        )

    def _receive(self, model: str, messages: list) -> None:
        if self._record_file is not None:
            record_event(self._record_file, {"event": RECEIVED_EVENT, "model": model, "messages": messages})


# The object that custom_handler in config/litellm.yaml points to. LiteLLM calls its methods
# directly and never constructs it, so it is created here, when LiteLLM imports this module.
mock_llm_provider = MockLLMProvider.from_settings()
