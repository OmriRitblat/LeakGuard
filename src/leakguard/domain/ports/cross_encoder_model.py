"""«interface» CrossEncoderModel."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class CrossEncoderModel(ABC):
    """Scores how closely a text matches each reference text."""

    @abstractmethod
    def score(self, text: str, examples: Sequence[str]) -> list[float]:
        """Return one score in [0, 1] per example, in the same order."""
