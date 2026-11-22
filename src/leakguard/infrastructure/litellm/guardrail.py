"""«LiteLLM hook» LeakGuardGuardrail (ADD 5.2.11, FR-01, PC-01)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litellm.integrations.custom_guardrail import CustomGuardrail

from leakguard.infrastructure.litellm.failure_policy import FailurePolicy
from leakguard.infrastructure.litellm.inspection_client import InspectionClient

if TYPE_CHECKING:
    from litellm.caching.caching import DualCache
    from litellm.proxy._types import UserAPIKeyAuth


class LeakGuardGuardrail(CustomGuardrail):
    """The LiteLLM pre-call hook.

    Builds an InspectionRequest from the LiteLLM request, calls the InspectionClient
    under its FailurePolicy, and applies the result.
    """

    def __init__(self, client: InspectionClient, failure_policy: FailurePolicy, **kwargs: Any) -> None:
        """``kwargs`` are LiteLLM's guardrail settings (guardrail_name, event_hook, default_on, ...)."""
        super().__init__(**kwargs)
        self._client = client
        self._failure_policy = failure_policy

    async def async_pre_call_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        cache: DualCache,
        data: dict,
        call_type: str,  # LiteLLM types it as a Literal of call types; the set grows between versions
    ) -> Exception | str | dict | None:
        """Inspect the request before LiteLLM forwards it to the provider.

        Post Blocked:  decision = BLOCK implies the request is rejected and never forwarded (FR-10).
        Post Redacted: decision = REDACT implies the messages in ``data`` are replaced by
                       result.approved_texts (FR-11); the returned dict is the modified ``data``.
        Post when the inspection did not complete, the user gets the FailurePolicy notice.
        """
        raise NotImplementedError
