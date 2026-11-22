"""SentenceTransformerBiEncoder."""

from __future__ import annotations

from collections.abc import Sequence

from leakguard.domain.ports.bi_encoder import BiEncoder
from leakguard.domain.ports.vector_index import Vector


class SentenceTransformerBiEncoder(BiEncoder):
    """BiEncoder on the sentence-transformers library. Loaded once at start-up."""

    def __init__(self, model_name: str, device: str) -> None:
        self._model_name = model_name
        self._device = device

    def embed(self, texts: Sequence[str]) -> list[Vector]:
        raise NotImplementedError
