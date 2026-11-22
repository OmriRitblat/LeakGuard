"""CrossEncoderStage (ADD 5.2.2)."""

from __future__ import annotations

from leakguard.domain.inspection.context import InspectionContext
from leakguard.domain.inspection.stage import InspectionStage, StageOutcome
from leakguard.domain.ports.cross_encoder_model import CrossEncoderModel


class CrossEncoderStage(InspectionStage):
    """Re-scores the UNCERTAIN candidates with a Cross-Encoder."""

    def __init__(self, model: CrossEncoderModel) -> None:
        self._model = model

    def process(self, context: InspectionContext) -> StageOutcome:
        """Call model.score(current_text, texts of the candidate's matches) for each UNCERTAIN candidate.

        Post: ce_score = the highest of those scores;
          ce_score >= ce_threshold -> EXPOSED, return DECIDED;
          otherwise                -> SAFE.
        """
        raise NotImplementedError
