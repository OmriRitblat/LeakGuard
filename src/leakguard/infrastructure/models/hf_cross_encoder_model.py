"""HfCrossEncoderModel."""

from __future__ import annotations

from collections.abc import Sequence

from leakguard.domain.ports.cross_encoder_model import CrossEncoderModel


class HfCrossEncoderModel(CrossEncoderModel):
    """CrossEncoderModel on a Hugging Face cross-encoder. Loaded once at start-up."""

    def __init__(self, model_name: str, device: str) -> None:
        self._model_name = model_name
        self._device = device

    def score(self, text: str, examples: Sequence[str]) -> list[float]:
        raise NotImplementedError
