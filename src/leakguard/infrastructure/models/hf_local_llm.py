"""HfLocalLlm."""

from __future__ import annotations

from leakguard.domain.ports.local_llm import LocalLlm


class HfLocalLlm(LocalLlm):
    """LocalLlm on a Hugging Face model run locally (FR-16). Slow on a CPU: seconds per example."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    def generate(self, prompt: str) -> str:
        raise NotImplementedError
