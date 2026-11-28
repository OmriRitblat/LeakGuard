"""Test doubles of the LeakGuard hook, registered in tests/utils/litellm_test.yaml (issue #12).

The real hook approves every request until the inspection pipeline is connected, so these
doubles stand in for the decisions it will make. Each one writes its own event to the mock
LLM's record file (mock_llm.record_file), so a test sees the hook and the mock LLM in one order.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException

from leakguard.config.settings import load_settings
from leakguard.infrastructure.litellm.guardrail import LeakGuardGuardrail
from leakguard.infrastructure.litellm.mock_llm_provider import record_event

if TYPE_CHECKING:
    from litellm.caching.caching import DualCache
    from litellm.proxy._types import UserAPIKeyAuth

# The request fields a client controls, recorded by SpyGuardrail (LiteLLM adds its own keys).
CLIENT_FIELDS = ("model", "messages", "stream", "temperature", "user")
HOOK_APPROVED = "hook_approved"
HOOK_REJECTED = "hook_rejected"
HOOK_REPLACED = "hook_replaced"
REJECTION_DETAIL = "Blocked by the LeakGuard test hook"
REPLACEMENT_MESSAGES = [{"role": "user", "content": "[REPLACED BY TEST HOOK]"}]


class _RecordingGuardrail(LeakGuardGuardrail):
    """Base of the doubles: writes hook events to the mock LLM's record file."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        record_file = load_settings().mock_llm.record_file
        if record_file is None:
            raise RuntimeError(
                "The hook doubles need mock_llm.record_file (set LEAKGUARD_MOCK_LLM__RECORD_FILE)"
            )
        self._record_file = record_file

    def _record(self, event: dict[str, Any]) -> None:
        record_event(self._record_file, event)


class SpyGuardrail(_RecordingGuardrail):
    """Runs the real LeakGuard hook and records what it received.

    The request fields a client controls are copied before the real hook runs; the event is
    written after the real hook returned, so it also marks the moment of approval.
    """

    async def async_pre_call_hook(
        self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: str
    ) -> Exception | str | dict | None:
        received = {key: copy.deepcopy(data.get(key)) for key in CLIENT_FIELDS}
        result = await super().async_pre_call_hook(user_api_key_dict, cache, data, call_type)
        self._record({"event": HOOK_APPROVED, "call_type": call_type, **received})
        return result


class RejectingGuardrail(_RecordingGuardrail):
    """Rejects every request. Records no message content, so the record file can be searched
    for leaked prompt text."""

    async def async_pre_call_hook(
        self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: str
    ) -> dict:
        self._record({"event": HOOK_REJECTED})
        raise HTTPException(status_code=400, detail=REJECTION_DETAIL)


class ReplacingGuardrail(_RecordingGuardrail):
    """Replaces the messages, as redaction will, and approves the modified request. Records no
    message content, so the record file can be searched for the original text."""

    async def async_pre_call_hook(
        self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: str
    ) -> dict:
        self._record({"event": HOOK_REPLACED})
        data["messages"] = [dict(message) for message in REPLACEMENT_MESSAGES]
        return data
