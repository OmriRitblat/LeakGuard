"""The InspectionRecord aggregate (ADD 5.2.10)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from leakguard.domain.common.enums import Decision
from leakguard.domain.common.value_objects import Finding


@dataclass
class InspectionRecord:
    """«aggregate root» The audit entry of one inspection (FR-28, FR-29).

    Holds no prompt text (NFR-05).

    Invariants:
      - ExposureMeansBlock: any SECRET_EXPOSURE finding implies decision = BLOCK;
      - NonNegativeLatency: latency_ms >= 0;
      - SecretFindingNamesSecret: SECRET_EXPOSURE findings have a secret_id;
      - snapshot_version = the version of the snapshot the inspection used (INV-05).
    """

    id: UUID
    timestamp: datetime
    user_id: UUID
    decision: Decision
    snapshot_version: int
    latency_ms: int
    findings: list[Finding] = field(default_factory=list)
