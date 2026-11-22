"""EmbeddingMatchStage (ADD 5.2.2)."""

from __future__ import annotations

from leakguard.domain.inspection.context import InspectionContext
from leakguard.domain.inspection.stage import InspectionStage, StageOutcome
from leakguard.domain.ports.bi_encoder import BiEncoder
from leakguard.domain.ports.vector_index import VectorIndex


class EmbeddingMatchStage(InspectionStage):
    """Embeds current_text and searches the vector index (FR-07).

    The index holds each secret's description, each prohibited detail of its
    exposure policy, and its exposure examples.

    max_matches_per_candidate (not in diagram v11; from config): only the best N
    matches are kept per candidate (ADD: for example 5), so the Cross-Encoder's
    cost stays bounded. None keeps every match (unlimited).
    """

    def __init__(
        self, bi_encoder: BiEncoder, index: VectorIndex, max_matches_per_candidate: int | None
    ) -> None:
        self._bi_encoder = bi_encoder
        self._index = index
        self._max_matches_per_candidate = max_matches_per_candidate

    def process(self, context: InspectionContext) -> StageOutcome:
        """Search with min_sim = the lowest pass_threshold in the snapshot and group the Matches by secret.

        Post: one Candidate per snapshot secret that has a match, with its matches
        attached; similarity = that secret's best match;
          similarity >= block_threshold                  -> EXPOSED, return DECIDED;
          pass_threshold <= similarity < block_threshold -> UNCERTAIN;
          similarity < pass_threshold                    -> no candidate.
        """
        raise NotImplementedError
