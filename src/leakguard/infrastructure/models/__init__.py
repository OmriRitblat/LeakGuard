"""Model adapters: SentenceTransformerBiEncoder, HfCrossEncoderModel, HfLocalLlm.

Each takes a ``model_name`` and a ``device`` (cpu | cuda), not in diagram v11, so the
model is chosen by configuration (config/leakguard.yaml, section ``models``).
"""
