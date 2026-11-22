"""FailurePolicy (ADD 5.2.11)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import Enum

from leakguard.domain.common.value_objects import InspectionResult


class FailureMode(Enum):
    """FailurePolicy.mode: what to do when no valid result arrives (FR-12, NFR-09, NFR-15)."""

    FAIL_CLOSED = "FAIL_CLOSED"  # block
    FAIL_OPEN = "FAIL_OPEN"      # allow


class FailurePolicy:
    """Retries once and falls back to BLOCK or ALLOW.

    Belongs to the hook, because only the hook sees every kind of failure: an
    exception or timeout inside the service, a LeakGuard service that is down or
    unreachable (UC-02 A2), and a malformed answer.

    Invariants:
      - PositiveTimeout: timeout_ms > 0;
      - OneRetry: max_attempts = 2 (the first attempt + one retry, FR-12).
    """

    def __init__(self, mode: FailureMode, timeout_ms: int, max_attempts: int = 2) -> None:
        self._mode = mode
        self._timeout_ms = timeout_ms
        self._max_attempts = max_attempts

    async def execute(self, run: Callable[[], Awaitable[InspectionResult]]) -> InspectionResult:
        """Run the inspection under the timeout and retry rules.

        Post Attempts: at most max_attempts calls of ``run``.
        Post Fallback: not result.completed implies decision = BLOCK if mode is
             FAIL_CLOSED, else ALLOW.
        Post Notice:   not result.completed implies result.notice <> ''.
        """
        raise NotImplementedError
