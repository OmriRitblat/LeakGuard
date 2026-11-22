"""«interface» InspectionStage (ADD 5.2.2)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from leakguard.domain.inspection.context import InspectionContext


class StageOutcome(Enum):
    """The result of InspectionStage.process: CONTINUE | DECIDED (DECIDED means BLOCK)."""

    CONTINUE = "CONTINUE"
    DECIDED = "DECIDED"


class InspectionStage(ABC):
    """One step of the inspection pipeline (FR-06).

    A stage reads the context, adds to it, and returns CONTINUE or DECIDED.
    Stages are stateless and shared between concurrent requests.
    """

    @abstractmethod
    def process(self, context: InspectionContext) -> StageOutcome:
        """Run this stage on one request's context."""
