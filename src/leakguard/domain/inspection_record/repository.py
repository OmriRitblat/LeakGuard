"""«interface» InspectionRecordRepository (ADD 5.2.10)."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from leakguard.domain.common.repository import Repository
from leakguard.domain.common.value_objects import Period
from leakguard.domain.inspection_record.inspection_record import InspectionRecord
from leakguard.domain.inspection_record.statistics import InspectionStats, StatsFilter


class InspectionRecordRepository(Repository[InspectionRecord]):
    """Persistence port of the InspectionRecord aggregate.

    Hint: index inspection_records on (user_id, created_at) and findings on (secret_id).
    """

    @abstractmethod
    def stats(self, filter: StatsFilter, period: Period) -> InspectionStats:
        """Aggregate the records that match the filter inside the period (FR-30)."""

    @abstractmethod
    def count_attempts(self, user_id: UUID, period: Period) -> int:
        """Count the user's inspections with a SECRET_EXPOSURE finding inside the period (FR-31)."""
