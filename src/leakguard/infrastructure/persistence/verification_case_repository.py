"""VerificationCaseRepositoryImpl."""

from __future__ import annotations

from leakguard.domain.verification.repository import VerificationCaseRepository
from leakguard.domain.verification.verification_case import VerificationCase
from leakguard.infrastructure.persistence.base_repository import BaseRepositoryImpl


class VerificationCaseRepositoryImpl(BaseRepositoryImpl[VerificationCase], VerificationCaseRepository):
    """VerificationCaseRepository on SQLAlchemy."""

    def list_pending(self) -> list[VerificationCase]:
        raise NotImplementedError
