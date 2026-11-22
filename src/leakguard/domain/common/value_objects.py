"""Value objects shared across layers. All are immutable (frozen dataclasses)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from leakguard.domain.common.enums import Decision, FindingType


@dataclass(frozen=True)
class Token:
    """«value object» Token: the identity of a logged-in caller.

    Passed as ``caller`` to every method a logged-in person calls; the API layer has
    already checked it.

    Invariant AdminFlag: is_admin = User.get(user_id).oclIsTypeOf(Admin).
    """

    value: str
    user_id: UUID
    is_admin: bool
    expires_at: datetime


@dataclass(frozen=True)
class InspectionRequest:
    """«value object» InspectionRequest: what the hook sends to LeakGuard (UC-02).

    ``user_ref`` is the employee identity forwarded by the chat client (an e-mail).
    """

    request_id: str
    user_ref: str
    texts: tuple[str, ...]
    received_at: datetime


@dataclass(frozen=True)
class Finding:
    """«value object» Finding: one PII match or one secret exposure.

    ``secret_id`` is set only for SECRET_EXPOSURE findings (InspectionRecord
    invariant SecretFindingNamesSecret).
    """

    type: FindingType
    secret_id: UUID | None
    score: float | None
    stage: str


@dataclass(frozen=True)
class InspectionResult:
    """«value object» InspectionResult: the answer of one inspection.

    Post-conditions it carries (InspectionService / FailurePolicy):
      - completed implies decision is not None;
      - any SECRET_EXPOSURE finding implies decision = BLOCK;
      - not completed implies notice <> '' (the user is told the inspection did not complete).
    """

    decision: Decision
    approved_texts: tuple[str, ...] = ()
    findings: tuple[Finding, ...] = ()
    notice: str = ""
    completed: bool = True


@dataclass(frozen=True)
class Period:
    """«value object» A closed time range used by the statistics (UC-08).

    Invariant ValidPeriod: start <= end (UC-08 A4).
    Not drawn in class diagram v11; added for the ``period`` parameters.
    """

    start: datetime
    end: datetime
