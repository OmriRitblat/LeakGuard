"""The VerificationCase aggregate (ADD 5.2.9)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from leakguard.domain.common.enums import Label


class CaseStatus(Enum):
    """VerificationCase.status: PENDING -> VERIFIED."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"


@dataclass
class VerificationCase:
    """«aggregate root» An uncertain inspection kept for the admin to review (FR-20).

    InspectionService creates it for each candidate still UNCERTAIN; the admin
    reviews it through SecretService.verify_case.

    A case is the only place a full prompt is kept (NFR-05): content is encrypted,
    and is cleared once it has been turned into an example.

    verified_label and created_at are not in diagram v11 (added on 2026-11-22).
    """

    id: UUID
    secret_id: UUID
    content: str  # encrypted at rest
    recommended_label: Label
    status: CaseStatus
    created_at: datetime
    verified_label: Label | None = None

    def verify(self, label: Label) -> None:
        """Record the admin's label.

        Pre  Pending:  status = PENDING (a verified case is never verified again).
        Post Verified: status = VERIFIED and verified_label = label.
        """
        raise NotImplementedError
