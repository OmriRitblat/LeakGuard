"""DecisionPolicy (ADD 5.2.3)."""

from __future__ import annotations

from leakguard.domain.common.enums import Decision
from leakguard.domain.inspection.context import InspectionContext


class DecisionPolicy:
    """Picks the final decision when no stage blocked.

    Fields:
      uncertain_decision: the configured decision for candidates still UNCERTAIN
        after the last stage (not in diagram v11; added on 2026-11-22).
    """

    def __init__(self, uncertain_decision: Decision) -> None:
        self._uncertain_decision = uncertain_decision

    def decide(self, context: InspectionContext) -> Decision:
        """Return ALLOW, REDACT or the configured decision.

        Pre  NotBlocked: no candidate is EXPOSED.
        Post AllSafe: every candidate SAFE implies result = REDACT if a PII finding exists, else ALLOW.
        Post StillUncertain: some candidate UNCERTAIN implies result = uncertain_decision.
        """
        raise NotImplementedError
