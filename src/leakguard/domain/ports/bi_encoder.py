"""«interface» BiEncoder."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from leakguard.domain.ports.vector_index import Vector


class BiEncoder(ABC):
    """Turns texts into embedding vectors (used for indexing and for EmbeddingMatchStage)."""

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[Vector]:
        """Return one vector per text, in the same order."""
