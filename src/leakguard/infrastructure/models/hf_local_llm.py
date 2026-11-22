"""HfLocalLlm."""

from __future__ import annotations

from leakguard.domain.ports.local_llm import LocalLlm


class HfLocalLlm(LocalLlm):
    """LocalLlm on a Hugging Face model run locally (FR-16). Slow on a CPU: seconds per example."""

    def __init__(self, model_name: str, device: str) -> None:
        self._model_name = model_name
        self._device = device

    def generate(self, prompt: str) -> str:
        raise NotImplementedError
