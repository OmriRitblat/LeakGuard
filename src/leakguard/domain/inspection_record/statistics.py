"""Value objects of the UC-08 statistics. Not drawn in class diagram v11 (added for the
untyped ``filter`` parameter and the untyped return values of the statistics methods)."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from leakguard.domain.common.enums import Decision


@dataclass(frozen=True)
class StatsFilter:
    """Which records to aggregate: by secret, by user, or (both None) all records."""

    secret_id: UUID | None = None
    user_id: UUID | None = None


@dataclass(frozen=True)
class InspectionStats:
    """Aggregated counts over a period (FR-30)."""

    total: int
    by_decision: dict[Decision, int] = field(default_factory=dict)
    exposure_attempts: int = 0


@dataclass(frozen=True)
class AttempterStats:
    """One user with unusually frequent exposure attempts (FR-31)."""

    user_id: UUID
    attempts: int
