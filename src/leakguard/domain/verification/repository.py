"""«interface» VerificationCaseRepository (ADD 5.2.9)."""

from __future__ import annotations

from abc import abstractmethod

from leakguard.domain.common.repository import Repository
from leakguard.domain.verification.verification_case import VerificationCase


class VerificationCaseRepository(Repository[VerificationCase]):
    """Persistence port of the VerificationCase aggregate."""

    @abstractmethod
    def list_pending(self) -> list[VerificationCase]:
        """Return every case with status PENDING (UC-07). An empty list is valid (UC-07 A1)."""
