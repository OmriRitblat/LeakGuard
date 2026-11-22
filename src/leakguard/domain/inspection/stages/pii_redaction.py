"""PiiRedactionStage (ADD 5.2.2)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from leakguard.domain.inspection.context import InspectionContext
from leakguard.domain.inspection.stage import InspectionStage, StageOutcome


class PiiType(Enum):
    """The PII kinds found by rules (FR-03). Not in diagram v11."""

    EMAIL = "EMAIL"
    NATIONAL_ID = "NATIONAL_ID"
    CREDIT_CARD = "CREDIT_CARD"


@dataclass(frozen=True)
class PiiRule:
    """«value object» One rule of PiiRedactionStage. Not in diagram v11 (it writes "rules: email, ID, card").

    A regex finds candidates; ``is_valid`` filters them (Luhn for card numbers,
    the check digit for national ID numbers).
    """

    pii_type: PiiType
    pattern: re.Pattern[str]
    placeholder: str

    def is_valid(self, candidate: str) -> bool:
        """Return True if the regex match is real PII (Luhn / check digit; always True for e-mail)."""
        raise NotImplementedError


class PiiRedactionStage(InspectionStage):
    """Finds e-mail addresses, national ID numbers and credit-card numbers by rules
    and replaces each with a type placeholder (FR-03, FR-04)."""

    def __init__(self, rules: Sequence[PiiRule]) -> None:
        self._rules: tuple[PiiRule, ...] = tuple(rules)

    def process(self, context: InspectionContext) -> StageOutcome:
        """Redact PII in context.current_text.

        Post: current_text holds no rule match; one Finding(type = PII) per match;
        always returns CONTINUE.
        """
        raise NotImplementedError
