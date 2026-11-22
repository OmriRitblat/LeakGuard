"""LeakGuard settings.

Sources, highest priority first:
  1. environment variables, prefix LEAKGUARD_ and ``__`` between levels,
     e.g. LEAKGUARD_MODELS__BI_ENCODER__DEVICE=cuda;
  2. the YAML file: $LEAKGUARD_CONFIG_FILE, or config/leakguard.yaml relative to
     the working directory.

Every value lives in the YAML file; the classes below hold no defaults, so a
missing or misspelled key stops start-up with a clear error.
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from leakguard.domain.common.enums import Decision
from leakguard.infrastructure.litellm.failure_policy import FailureMode

DEFAULT_CONFIG_FILE = "config/leakguard.yaml"
CONFIG_FILE_ENV = "LEAKGUARD_CONFIG_FILE"


class _Section(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InspectionSettings(_Section):
    """InspectionService, DecisionPolicy and EmbeddingMatchStage."""

    time_limit_ms: int = Field(gt=0, description="InspectionService deadline per request")
    uncertain_decision: Decision = Field(description="DecisionPolicy: decision for candidates still UNCERTAIN")
    max_matches_per_candidate: int | None = Field(
        gt=0, description="EmbeddingMatchStage: top matches kept per candidate; None = unlimited"
    )


class FailurePolicySettings(_Section):
    """The hook's FailurePolicy (FR-12, NFR-09, NFR-15)."""

    mode: FailureMode
    timeout_ms: int = Field(gt=0, description="PositiveTimeout")
    max_attempts: Literal[2] = Field(description="OneRetry: the first attempt + one retry (FR-12)")


class ModelSettings(_Section):
    """One model: its Hugging Face id and the device it runs on."""

    name: str = Field(min_length=1)
    device: str = Field(pattern=r"^(cpu|cuda(:\d+)?)$", description="cpu | cuda | cuda:<n>")


class ModelsSettings(_Section):
    """Every model of the system, each with its own device.

    A later model (e.g. a JEV-class local decision model) is one more field of type
    ModelSettings (or ModelSettings | None while it is optional).
    """

    bi_encoder: ModelSettings
    cross_encoder: ModelSettings
    local_llm: ModelSettings | None = Field(description="None disables the local LLM (example generation, judge stage)")


class VectorIndexSettings(_Section):
    """PgVectorIndex."""

    max_results: int = Field(gt=0, description="LIMIT on search, as a safety cap")


class StatisticsSettings(_Section):
    """StatisticsService."""

    attempt_limit: int = Field(gt=0, description="exposure attempts per user per day above which a user is flagged (FR-31)")


class Settings(BaseSettings):
    """All LeakGuard settings. Build it with load_settings()."""

    model_config = SettingsConfigDict(
        env_prefix="LEAKGUARD_",
        env_nested_delimiter="__",
        extra="forbid",
        frozen=True,
    )

    inspection: InspectionSettings
    failure_policy: FailurePolicySettings
    models: ModelsSettings
    vector_index: VectorIndexSettings
    statistics: StatisticsSettings

    @model_validator(mode="after")
    def _service_answers_before_hook_gives_up(self) -> Settings:
        # ADD 5.2.1: time_limit_ms must be below FailurePolicy.timeout_ms.
        if self.inspection.time_limit_ms >= self.failure_policy.timeout_ms:
            raise ValueError(
                "inspection.time_limit_ms must be lower than failure_policy.timeout_ms "
                f"({self.inspection.time_limit_ms} >= {self.failure_policy.timeout_ms})"
            )
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_file = os.environ.get(CONFIG_FILE_ENV, DEFAULT_CONFIG_FILE)
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_file, yaml_file_encoding="utf-8"),
        )


def load_settings() -> Settings:
    """Read and validate the settings. Raises FileNotFoundError if the YAML file is missing,
    and pydantic.ValidationError if a value is missing or invalid."""
    yaml_file = os.environ.get(CONFIG_FILE_ENV, DEFAULT_CONFIG_FILE)
    if not os.path.isfile(yaml_file):
        raise FileNotFoundError(
            f"LeakGuard config file not found: {os.path.abspath(yaml_file)} "
            f"(set {CONFIG_FILE_ENV} or run from the project root)"
        )
    return Settings()
