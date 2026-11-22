"""StatisticsService (ADD 5.2.10)."""

from __future__ import annotations

from uuid import UUID

from leakguard.domain.common.value_objects import Period, Token
from leakguard.domain.inspection_record.repository import InspectionRecordRepository
from leakguard.domain.inspection_record.statistics import AttempterStats, InspectionStats


class StatisticsService:
    """UC-08: statistics by secret or by user, and users with unusually frequent
    exposure attempts (FR-30, FR-31). Read-only.

    Fields:
      attempt_limit: the "unusually frequent" limit (attempts per user per day), a
        configuration value per the ADD hint. Not in diagram v11.
    """

    def __init__(self, records: InspectionRecordRepository, attempt_limit: int) -> None:
        self._records = records
        self._attempt_limit = attempt_limit

    def by_secret(self, caller: Token, secret_id: UUID, period: Period) -> InspectionStats:
        """Statistics of one secret.

        Pre  caller.is_admin (UC-08 A2); period.start <= period.end (UC-08 A4).
        Post ReadOnly: no record changes.
        """
        raise NotImplementedError

    def by_user(self, caller: Token, user_id: UUID, period: Period) -> InspectionStats:
        """Statistics of one user.

        Pre  Admin: caller.is_admin (UC-08 A2).
        Pre  ValidPeriod: period.start <= period.end (UC-08 A4).
        Pre  Exists: the user exists (UC-08 A3).
        Post ReadOnly: no record changes.
        """
        raise NotImplementedError

    def frequent_attempters(self, caller: Token, period: Period) -> list[AttempterStats]:
        """Users whose exposure attempts exceed attempt_limit (FR-31).

        Pre  caller.is_admin; period.start <= period.end.
        Post ReadOnly: no record changes.
        """
        raise NotImplementedError
