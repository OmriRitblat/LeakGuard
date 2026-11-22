"""«interface» LocalLlm."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LocalLlm(ABC):
    """A locally hosted LLM: generates examples (FR-16) and, later, judges uncertain candidates."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the model's completion of the prompt."""
