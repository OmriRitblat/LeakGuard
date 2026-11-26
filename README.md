# LeakGuard

Semantic DLP guardrail for LiteLLM Proxy (BGU Software Engineering final project).

**Status: code skeleton.** Packages, classes, interfaces, fields and method signatures
from `LeakGuard_class_diagram_v11` and the ADD (5.2 Class Description). Method bodies
raise `NotImplementedError`. Each docstring carries the ADD's pre/post-conditions.
The initial packages, class signatures and interfaces follow the class
diagram and ADD. The PostgreSQL schema and database integration tests
have been added; most application, repository and adapter method bodies
are still placeholders.

## Layout

```
src/leakguard/
  domain/                      DOMAIN / BUSINESS LAYER
    common/                    Label, Decision, FindingType, Token, InspectionRequest,
                               InspectionResult, Finding, Period, Repository[T], errors
    secret/                    «aggregate» Secret, ExposurePolicy, ViewPermission,
                               LabeledExample, SecretDraft, SecretRepository
    user/                      «aggregate» User, Admin, UserRepository
    verification/              «aggregate» VerificationCase, VerificationCaseRepository
    inspection_record/         «aggregate» InspectionRecord, InspectionRecordRepository, stats types
    inspection/                InspectionPipeline, InspectionStage, DecisionPolicy,
                               InspectionContext, Candidate, Match, SecretSnapshot, SecretRule
      stages/                  PiiRedactionStage, EmbeddingMatchStage, CrossEncoderStage,
                               LocalLlmJudgeStage (later version)
    ports/                     VectorIndex, BiEncoder, CrossEncoderModel, LocalLlm,
                               PasswordHasher, TokenIssuer
  application/                 APPLICATION LAYER
                               InspectionService, SecretService, SecretAccessService,
                               UserService, StatisticsService
  config/                      Settings (pydantic-settings) + load_settings()
  infrastructure/              INFRASTRUCTURE LAYER
    litellm/                   LeakGuardGuardrail (LiteLLM hook), FailurePolicy,
                               InspectionClient, InProcessInspectionClient (POC),
                               HttpInspectionClient (Alpha)
    persistence/               BaseRepositoryImpl[T] + 4 repository implementations
    security/                  CryptoService, Argon2PasswordHasher, JwtTokenIssuer
    vector/                    PgVectorIndex
    models/                    SentenceTransformerBiEncoder, HfCrossEncoderModel, HfLocalLlm
config/leakguard.yaml          all tuning values (inspection, failure policy, models, vector index, statistics)
tests/                         pytest tests (test_ci.py is a placeholder)
.github/workflows/ci.yml       GitHub Actions: runs pytest on Python 3.11 on every push to main and every PR
```

## How the diagram maps to code

| Diagram | Code |
| :- | :- |
| «interface» | `abc.ABC` with `@abstractmethod` |
| dashed triangle (realizes) / solid triangle (extends) | subclassing |
| «value object» | `@dataclass(frozen=True)`; its list fields are tuples |
| entity / aggregate root | `@dataclass` |
| composition (filled diamond), e.g. Secret ◆— LabeledExample | owned field, `examples: list[LabeledExample]` |
| aggregation (hollow diamond), InspectionPipeline ◇— InspectionStage | `stages` passed in the constructor |
| association (open arrow) to a port/repository | constructor parameter stored as a private field |
| `- field` in a service or adapter | `self._field` |
| `A \| B` inline enum | an `Enum` class next to its owner |

Async: only the inspection entry points are `async` (the LiteLLM hook,
`InspectionClient.inspect`, `InspectionService.inspect`, `FailurePolicy.execute`).
The pipeline, stages and repositories are synchronous.

## Differences from class diagram v11 (agreed 2026-11-22)

- `VectorIndex.upsert` takes `text` (search must return it for the Cross-Encoder); new `VectorIndex.contains(ref_id)`.
- `DecisionPolicy.uncertain_decision: Decision`.
- `VerificationCase.verified_label` and `VerificationCase.created_at`.
- `SecretService._generate_examples(secret_id)` (background example generation, FR-16).
- `LeakGuardGuardrail` extends LiteLLM's `CustomGuardrail` and uses the real
  `async_pre_call_hook(user_api_key_dict, cache, data, call_type)` signature.
- New types for untyped parameters and results: `SecretDraft`/`ExampleDraft`, `Period`,
  `StatsFilter`, `InspectionStats`, `AttempterStats`, `PiiRule`/`PiiType`, domain errors.
- Constructor settings the diagram leaves out: `StatisticsService.attempt_limit`,
  `JwtTokenIssuer.signing_key`/`lifetime`, `PgVectorIndex.session`/`crypto`/`max_results`,
  `EmbeddingMatchStage.max_matches_per_candidate`, `model_name` and `device` on the three
  model adapters.
- `UserRepository.find_by_email` returns `User | None`.

## Configuration

All tuning values live in `config/leakguard.yaml` and are read into a typed, frozen
`Settings` object:

```python
from leakguard.config.settings import load_settings
settings = load_settings()
settings.failure_policy.timeout_ms   # 7000
```

### Sections

| Section | Keys | Used by |
| :- | :- | :- |
| `inspection` | `time_limit_ms`, `uncertain_decision`, `max_matches_per_candidate` (`null` = unlimited) | InspectionService, DecisionPolicy, EmbeddingMatchStage |
| `failure_policy` | `mode` (FAIL_CLOSED / FAIL_OPEN), `timeout_ms`, `max_attempts` (fixed at 2: one retry, FR-12) | the hook's FailurePolicy |
| `models` | `bi_encoder`, `cross_encoder`, `local_llm` (`null` = disabled), each with `name` and `device` (`cpu`, `cuda` or `cuda:<n>`) | the three model adapters |
| `vector_index` | `max_results` | PgVectorIndex |
| `statistics` | `attempt_limit` | StatisticsService |

No secrets are in this file. The database URL, encryption key, JWT key and service
token will come from environment variables when they are added.

### Two timers

`inspection.time_limit_ms` is how long InspectionService may work on one request;
when it runs out, the service answers "not completed". `failure_policy.timeout_ms` is
how long the hook waits for that answer; when it runs out, the hook retries once,
then falls back to BLOCK (FAIL_CLOSED) or ALLOW (FAIL_OPEN). The first must be lower
than the second, so the service answers before the hook gives up. Worst-case wait for
the user: `max_attempts × timeout_ms` (2 × 7000 = 14 s).

### How it is read

`src/leakguard/config/settings.py` defines one pydantic class per section; the field
types are the validation. `load_settings()`:

1. checks that the YAML file exists (`$LEAKGUARD_CONFIG_FILE`, or
   `config/leakguard.yaml` relative to the working directory, so run from the project root);
2. reads the sources, highest priority first: values passed in code (tests) >
   environment variables `LEAKGUARD_<SECTION>__<KEY>` (e.g.
   `LEAKGUARD_MODELS__BI_ENCODER__DEVICE=cuda`) > the YAML file;
3. validates every field (types, ranges, enums, the device pattern, unknown keys)
   and checks `time_limit_ms < timeout_ms`;
4. returns a frozen `Settings` object, or raises `FileNotFoundError` /
   `pydantic.ValidationError` with a message naming the bad key.

The classes contain no defaults: every value lives in the YAML file.

### When it runs

Only when `load_settings()` is called; importing the module reads nothing. Nothing
calls it yet. The start-up code (to be written) will call it once per process: in the
POC when LiteLLM starts and creates the hook, in the Alpha when the LeakGuard service
starts. A change to the YAML therefore takes effect after a restart. The classes never
read the configuration themselves; the start-up code passes plain values to their
constructors.

## Not yet in the skeleton

FastAPI routers (the API layer that checks `caller`),
encryption-key/JWT/service-token configuration and management,
the wiring that builds application services from `Settings`,
and the management UI.

SQLAlchemy ORM table definitions and local database setup are now
available; repository operations and encryption are not yet implemented.

## Local PostgreSQL database (development)

LeakGuard's local database runs in Docker Compose (PostgreSQL 16 with pgvector).
Each developer runs a separate local database, not a shared one.

**Getting started:** [Database setup, initialization, testing and troubleshooting](docs/database.md).

The database includes the 10 tables defined in the approved ERD.

**Current limitations:** CryptoService, repository operations and
fixture loading are not yet implemented. Do not store real
organizational secrets.

## Development

```bash
pip install -e ".[dev]"            # core + pytest (what CI installs)
pip install -e ".[dev,litellm]"    # + LiteLLM, for the guardrail hook
pip install -e ".[dev,all]"        # + sentence-transformers/transformers (pulls in PyTorch)
pytest
```
