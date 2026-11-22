"""InspectionRecordRepositoryImpl."""

from __future__ import annotations

from uuid import UUID

from leakguard.domain.common.value_objects import Period
from leakguard.domain.inspection_record.inspection_record import InspectionRecord
from leakguard.domain.inspection_record.repository import InspectionRecordRepository
from leakguard.domain.inspection_record.statistics import InspectionStats, StatsFilter
from leakguard.infrastructure.persistence.base_repository import BaseRepositoryImpl


class InspectionRecordRepositoryImpl(BaseRepositoryImpl[InspectionRecord], InspectionRecordRepository):
    """InspectionRecordRepository on SQLAlchemy."""

    def stats(self, filter: StatsFilter, period: Period) -> InspectionStats:
        raise NotImplementedError

    def count_attempts(self, user_id: UUID, period: Period) -> int:
        raise NotImplementedError
