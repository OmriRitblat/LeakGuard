"""InspectionPipeline (ADD 5.2.2)."""

from __future__ import annotations

from collections.abc import Sequence

from leakguard.domain.common.value_objects import InspectionResult
from leakguard.domain.inspection.context import InspectionContext
from leakguard.domain.inspection.decision_policy import DecisionPolicy
from leakguard.domain.inspection.stage import InspectionStage


class InspectionPipeline:
    """Runs its stages in order on one InspectionContext.

    Stops early when a stage returns DECIDED (a BLOCK); otherwise asks the
    DecisionPolicy for the final decision. Built once at start-up, because the
    models take seconds to load.

    Aggregation: InspectionPipeline <>-- 1..* InspectionStage.

    Invariants:
      - NotEmpty: stages is not empty;
      - PiiFirst: the first stage is a PiiRedactionStage (FR-05: secrets are
        checked on the redacted text).
    """

    def __init__(self, stages: Sequence[InspectionStage], decision_policy: DecisionPolicy) -> None:
        self._stages: list[InspectionStage] = list(stages)
        self._decision_policy = decision_policy

    def run(self, context: InspectionContext) -> InspectionResult:
        """Inspect one request.

        Pre  Fresh: context has no findings, no candidates and no decision.
        Post AnyExposureBlocks: an EXPOSED candidate implies decision = BLOCK (FR-08).
        Post RedactOnlyPii: decision = REDACT implies a PII finding exists.
        Post ApprovedText: decision <> BLOCK implies approved_texts = (context.current_text,).
        """
        raise NotImplementedError
