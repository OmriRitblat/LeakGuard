"""Match: one stored reference text of a secret returned by a vector search (ADD 5.2.3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class MatchKind(Enum):
    """Match.kind: what the indexed text is."""

    DESCRIPTION = "DESCRIPTION"      # the secret's description
    POLICY_DETAIL = "POLICY_DETAIL"  # one prohibited detail of its ExposurePolicy
    EXAMPLE = "EXAMPLE"              # one EXPOSURE LabeledExample


@dataclass(frozen=True)
class Match:
    """«value object» A stored reference text the Cross-Encoder compares the prompt with.

    Invariants:
      - SimilarityRange: -1 <= similarity <= 1;
      - KnownKind: kind is DESCRIPTION, POLICY_DETAIL or EXAMPLE.
    """

    ref_id: UUID
    secret_id: UUID
    kind: MatchKind
    text: str
    similarity: float
