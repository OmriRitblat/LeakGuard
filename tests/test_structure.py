"""Structure checks for the skeleton: every module imports, and every realization /
generalization arrow of class diagram v11 holds in the code."""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest

import leakguard

LITELLM_MODULES = {"leakguard.infrastructure.litellm.guardrail"}


def _all_modules() -> list[str]:
    return [m.name for m in pkgutil.walk_packages(leakguard.__path__, prefix="leakguard.")]


@pytest.mark.parametrize("module_name", _all_modules())
def test_module_imports(module_name: str) -> None:
    if module_name in LITELLM_MODULES:
        pytest.importorskip("litellm")
    importlib.import_module(module_name)


# (implementation, interface) pairs: the dashed and solid triangle arrows of the diagram.
REALIZATIONS = [
    ("infrastructure.litellm.in_process_client.InProcessInspectionClient", "infrastructure.litellm.inspection_client.InspectionClient"),
    ("infrastructure.litellm.http_client.HttpInspectionClient", "infrastructure.litellm.inspection_client.InspectionClient"),
    ("domain.inspection.stages.pii_redaction.PiiRedactionStage", "domain.inspection.stage.InspectionStage"),
    ("domain.inspection.stages.embedding_match.EmbeddingMatchStage", "domain.inspection.stage.InspectionStage"),
    ("domain.inspection.stages.cross_encoder.CrossEncoderStage", "domain.inspection.stage.InspectionStage"),
    ("domain.inspection.stages.local_llm_judge.LocalLlmJudgeStage", "domain.inspection.stage.InspectionStage"),
    ("domain.user.user.Admin", "domain.user.user.User"),
    ("infrastructure.security.argon2_password_hasher.Argon2PasswordHasher", "domain.ports.password_hasher.PasswordHasher"),
    ("infrastructure.security.jwt_token_issuer.JwtTokenIssuer", "domain.ports.token_issuer.TokenIssuer"),
    ("infrastructure.persistence.base_repository.BaseRepositoryImpl", "domain.common.repository.Repository"),
    ("infrastructure.persistence.secret_repository.SecretRepositoryImpl", "domain.secret.repository.SecretRepository"),
    ("infrastructure.persistence.secret_repository.SecretRepositoryImpl", "infrastructure.persistence.base_repository.BaseRepositoryImpl"),
    ("infrastructure.persistence.user_repository.UserRepositoryImpl", "domain.user.repository.UserRepository"),
    ("infrastructure.persistence.user_repository.UserRepositoryImpl", "infrastructure.persistence.base_repository.BaseRepositoryImpl"),
    ("infrastructure.persistence.verification_case_repository.VerificationCaseRepositoryImpl", "domain.verification.repository.VerificationCaseRepository"),
    ("infrastructure.persistence.verification_case_repository.VerificationCaseRepositoryImpl", "infrastructure.persistence.base_repository.BaseRepositoryImpl"),
    ("infrastructure.persistence.inspection_record_repository.InspectionRecordRepositoryImpl", "domain.inspection_record.repository.InspectionRecordRepository"),
    ("infrastructure.persistence.inspection_record_repository.InspectionRecordRepositoryImpl", "infrastructure.persistence.base_repository.BaseRepositoryImpl"),
    ("domain.secret.repository.SecretRepository", "domain.common.repository.Repository"),
    ("domain.user.repository.UserRepository", "domain.common.repository.Repository"),
    ("domain.verification.repository.VerificationCaseRepository", "domain.common.repository.Repository"),
    ("domain.inspection_record.repository.InspectionRecordRepository", "domain.common.repository.Repository"),
    ("infrastructure.vector.pg_vector_index.PgVectorIndex", "domain.ports.vector_index.VectorIndex"),
    ("infrastructure.models.sentence_transformer_bi_encoder.SentenceTransformerBiEncoder", "domain.ports.bi_encoder.BiEncoder"),
    ("infrastructure.models.hf_cross_encoder_model.HfCrossEncoderModel", "domain.ports.cross_encoder_model.CrossEncoderModel"),
    ("infrastructure.models.hf_local_llm.HfLocalLlm", "domain.ports.local_llm.LocalLlm"),
]


def _load(path: str) -> type:
    module, _, name = f"leakguard.{path}".rpartition(".")
    return getattr(importlib.import_module(module), name)


@pytest.mark.parametrize(("impl", "iface"), REALIZATIONS)
def test_realization(impl: str, iface: str) -> None:
    impl_cls, iface_cls = _load(impl), _load(iface)
    assert issubclass(impl_cls, iface_cls)
    # A concrete class must implement every abstract method of its interface.
    if not impl.startswith("domain.") or "stages" in impl:
        assert not inspect.isabstract(impl_cls), sorted(getattr(impl_cls, "__abstractmethods__", ()))


def test_guardrail_is_a_litellm_custom_guardrail() -> None:
    pytest.importorskip("litellm")
    from litellm.integrations.custom_guardrail import CustomGuardrail

    from leakguard.infrastructure.litellm.guardrail import LeakGuardGuardrail

    assert issubclass(LeakGuardGuardrail, CustomGuardrail)
    params = list(inspect.signature(LeakGuardGuardrail.async_pre_call_hook).parameters)
    assert params == ["self", "user_api_key_dict", "cache", "data", "call_type"]
