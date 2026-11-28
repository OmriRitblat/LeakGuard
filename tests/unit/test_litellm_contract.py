"""Contract tests for the LiteLLM integration (PC-01, R4).

They fail when the installed LiteLLM is not the pinned version, when LiteLLM changes the
pre-call hook interface, or when config/litellm.yaml stops loading the LeakGuard guardrail.
"""

from __future__ import annotations

import importlib.metadata
import inspect
import re
import tomllib
from pathlib import Path

import pytest
import yaml

pytest.importorskip("litellm")

from litellm.integrations.custom_guardrail import CustomGuardrail  # noqa: E402
from litellm.proxy.types_utils.utils import get_instance_fn  # noqa: E402

from leakguard.infrastructure.litellm.guardrail import LeakGuardGuardrail  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LITELLM_CONFIG = PROJECT_ROOT / "config" / "litellm.yaml"
HOOK_PARAMETERS = ["self", "user_api_key_dict", "cache", "data", "call_type"]


def _pinned_litellm_version() -> str:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirement = pyproject["project"]["optional-dependencies"]["litellm"][0]
    match = re.fullmatch(r"litellm(\[[^\]]*\])?==(?P<version>[\w.]+)", requirement)
    assert match, f"litellm must be pinned with '==', found {requirement!r}"
    return match["version"]


def _load_config() -> dict:
    return yaml.safe_load(LITELLM_CONFIG.read_text(encoding="utf-8"))


def _leakguard_guardrail_params() -> dict:
    entries = [g for g in _load_config()["guardrails"] if g["guardrail_name"] == "leakguard"]
    assert len(entries) == 1, "config/litellm.yaml must register exactly one 'leakguard' guardrail"
    return entries[0]["litellm_params"]


# 1
def test_installed_litellm_is_the_pinned_version():
    assert importlib.metadata.version("litellm") == _pinned_litellm_version()


# 2
def test_litellm_pre_call_hook_interface_is_unchanged():
    hook = CustomGuardrail.async_pre_call_hook
    assert inspect.iscoroutinefunction(hook)
    assert list(inspect.signature(hook).parameters) == HOOK_PARAMETERS


# 3
def test_leakguard_guardrail_implements_the_hook_interface():
    assert issubclass(LeakGuardGuardrail, CustomGuardrail)
    hook = LeakGuardGuardrail.async_pre_call_hook
    assert inspect.iscoroutinefunction(hook)
    assert list(inspect.signature(hook).parameters) == HOOK_PARAMETERS


# 4
def test_litellm_loads_and_constructs_the_configured_guardrail():
    params = _leakguard_guardrail_params()

    guardrail_class = get_instance_fn(params["guardrail"], config_file_path=str(LITELLM_CONFIG))
    assert guardrail_class is LeakGuardGuardrail

    # The arguments LiteLLM 1.108.20 passes (guardrail_registry), plus one extra setting.
    guardrail = guardrail_class(
        guardrail_name="leakguard",
        event_hook=params["mode"],
        default_on=params["default_on"],
        fail_on_error=True,
    )
    assert guardrail.guardrail_name == "leakguard"
    assert guardrail.event_hook == "pre_call"
    assert guardrail.default_on is True


# 5
def test_config_runs_the_guardrail_on_every_request_and_keeps_the_key_out():
    params = _leakguard_guardrail_params()
    assert params["mode"] == "pre_call"
    assert params["default_on"] is True
    assert _load_config()["general_settings"]["master_key"] == "os.environ/LITELLM_MASTER_KEY"
