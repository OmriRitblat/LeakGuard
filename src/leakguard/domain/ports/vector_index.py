"""«interface» VectorIndex."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from leakguard.domain.inspection.match import Match, MatchKind

Vector = Sequence[float]


class VectorIndex(ABC):
    """Stores the reference vectors of the secrets and finds those close to a prompt.

    Each row is one reference text: a secret's description (ref_id = secret_id),
    one prohibited detail of its ExposurePolicy, or one TRAIN EXPOSURE example
    (ref_id = example id).
    """

    @abstractmethod
    def search(self, vector: Vector, min_sim: float) -> list[Match]:
        """Return every row with similarity >= min_sim, with a LIMIT as a safety cap."""

    @abstractmethod
    def upsert(self, ref_id: UUID, secret_id: UUID, kind: MatchKind, text: str, vector: Vector) -> None:
        """Insert this reference text, or replace it if ref_id is already indexed.

        ``text`` is not in diagram v11 (added on 2026-11-22): search must return it in
        each Match, because the Cross-Encoder compares the prompt with the text.
        """

    @abstractmethod
    def remove_secret(self, secret_id: UUID) -> None:
        """Delete every row of this secret (FR-19)."""

    @abstractmethod
    def contains(self, ref_id: UUID) -> bool:
        """Return True if ref_id is indexed. Not in diagram v11; used by the ADD's post-conditions."""
