"""LocalLlmJudgeStage (ADD 5.2.2). Later version: not in the POC or the Alpha pipeline by default."""

from __future__ import annotations

from leakguard.domain.inspection.context import InspectionContext
from leakguard.domain.inspection.stage import InspectionStage, StageOutcome
from leakguard.domain.ports.local_llm import LocalLlm


class LocalLlmJudgeStage(InspectionStage):
    """Asks a local LLM about candidates still UNCERTAIN, given the secret's policy text and its matches."""

    def __init__(self, llm: LocalLlm) -> None:
        self._llm = llm

    def process(self, context: InspectionContext) -> StageOutcome:
        """Post: each remaining UNCERTAIN candidate becomes EXPOSED or SAFE; DECIDED if any is EXPOSED."""
        raise NotImplementedError
