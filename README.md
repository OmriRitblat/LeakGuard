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
                               HttpInspectionClient (Alpha), MockLLMProvider (POC test provider)
    persistence/               BaseRepositoryImpl[T] + 4 repository implementations
    security/                  CryptoService, Argon2PasswordHasher, JwtTokenIssuer
    vector/                    PgVectorIndex
    models/                    SentenceTransformerBiEncoder, HfCrossEncoderModel, HfLocalLlm
config/leakguard.yaml          all tuning values (inspection, failure policy, models, vector index, statistics, mock LLM);
                               tests use it too and override single values through LEAKGUARD_* variables
config/litellm.yaml            LiteLLM Proxy: the leakguard guardrail and the leakguard-mock model
tests/                         pytest tests (test_ci.py is a placeholder)
  utils/                       LiteLLM proxy helper (litellm_proxy.py), hook test doubles (litellm_doubles.py)
    litellm_test.yaml          test-only LiteLLM config: the mock LLM with the hook test doubles
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
- `LeakGuardGuardrail.__init__(client=None, failure_policy=None, **kwargs)`: LiteLLM creates
  the hook from `config/litellm.yaml`, so `client` and `failure_policy` are optional until the
  start-up wiring exists. Until then the hook approves every request unchanged.
- New types for untyped parameters and results: `SecretDraft`/`ExampleDraft`, `Period`,
  `StatsFilter`, `InspectionStats`, `AttempterStats`, `PiiRule`/`PiiType`, domain errors.
- Constructor settings the diagram leaves out: `StatisticsService.attempt_limit`,
  `JwtTokenIssuer.signing_key`/`lifetime`, `PgVectorIndex.session`/`crypto`/`max_results`,
  `EmbeddingMatchStage.max_matches_per_candidate`, `model_name` and `device` on the three
  model adapters.
- `UserRepository.find_by_email` returns `User | None`.
- `MockLLMProvider` (`infrastructure/litellm`) and the `mock_llm` settings section: POC test
  infrastructure that is not in the diagram. It stands in for the external LLM provider behind
  the `leakguard-mock` model (issue #12).

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
| `mock_llm` | `record_file` (`null` = off; a path = one JSON line per request the mock LLM receives) | MockLLMProvider |

No secrets are stored in the YAML configuration. Database credentials, the encryption key and the LiteLLM master key are configured through environment variables. JWT and service-token configuration will be added in later development stages.

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

FastAPI routers, JWT/service-token configuration and management, application startup wiring, and the management UI are not yet implemented.


SQLAlchemy ORM models, PostgreSQL infrastructure, AES-256-GCM encryption, and shared pytest fixtures are implemented. Repository operations, full TRAIN dataset seeding, and application startup integration are still pending.


## POC Dataset

The synthetic PayShield dataset contains TRAIN data for secret definitions, exposure policies, and labeled examples, alongside separate EVAL prompts with expected outcomes.

For dataset structure, labeling conventions, and evaluation cases, see the [POC Dataset README](datasets/leakguard_poc/README.md).

## Local PostgreSQL database (development)

LeakGuard's local database runs in Docker Compose (PostgreSQL 16 with pgvector).
Each developer runs a separate local database, not a shared one.

**Getting started:** [Database setup, initialization, testing and troubleshooting](docs/database.md).

The database includes the 10 tables defined in the approved ERD.


**Current limitations:** The database schema, encryption infrastructure, and shared testing fixtures are implemented. Full TRAIN dataset seeding, repository integration, and application startup wiring are still pending.


## Local Encryption Setup (Development)

LeakGuard uses AES-256-GCM to encrypt sensitive organizational information before storing it in PostgreSQL.

Each developer uses a separate local encryption key, stored in their `.env` file. The key is generated once during local setup and reused across application restarts.

### First-Time Setup

First, complete the local database setup described in [Database Setup](docs/database.md), including creating `.env` and installing the Python dependencies.

Then, from the project root, generate the encryption key:

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\python.exe scripts/generate_encryption_key.py
```

**Linux / macOS:**

```bash
.venv/bin/python scripts/generate_encryption_key.py
```

The script automatically:

- Generates a cryptographically secure 32-byte AES-256 key.
- Encodes the key in Base64 and stores it as `LEAKGUARD_ENCRYPTION_KEY` in `.env`.
- Preserves existing environment variables, including PostgreSQL settings.
- Does not overwrite an existing non-empty encryption key.
- Does not print the encryption key.

The script only needs to be run during initial setup. Re-running it is safe because an existing key will not be replaced.

### During Normal Operation

No additional key-generation step is required.

The `create_crypto_service_from_env()` function in `src/leakguard/config/encryption.py` loads the existing key and creates a `CryptoService` instance.

Integration with the application startup and persistence repositories will be completed in a later development stage.

### Security Notes

- Never commit `.env` or an actual encryption key to Git.
- Never replace a lost key if encrypted data already exists. Data encrypted with the original key cannot be decrypted using a new key.
- The key-generation script is intended for local development environments.
- Shared and production environments will require managed encryption keys.
- Do not store real organizational secrets during the POC.


## LiteLLM Proxy (development)

LiteLLM is pinned exactly to `litellm[proxy]==1.108.20` (LTS) in `pyproject.toml`; releases
1.82.7, 1.82.8 and 1.107.0 were compromised on PyPI. `config/litellm.yaml` registers the
`leakguard` pre-call guardrail on every request and a mock model, `leakguard-mock`, served by
`MockLLMProvider` (registered under `litellm_settings.custom_provider_map`). The mock calls no
real provider, so no API key is needed.

From the project root, after creating `.env`:

```bash
python scripts/generate_litellm_master_key.py   # writes LITELLM_MASTER_KEY to .env
litellm --config config/litellm.yaml            # http://localhost:4000
```

Requests must send `Authorization: Bearer <LITELLM_MASTER_KEY>`.

### Seeing what reaches the LLM

The mock LLM answers with the messages it received after the hook, as JSON
(`{"received_messages": [...]}`), for normal and streaming (`"stream": true`) requests:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>" -H "Content-Type: application/json" \
  -d '{"model": "leakguard-mock", "messages": [{"role": "user", "content": "hello"}]}'
```

To also record every request the mock LLM receives, set `mock_llm.record_file` in
`config/leakguard.yaml`, or `LEAKGUARD_MOCK_LLM__RECORD_FILE=<path>`, before starting the
proxy. Each request becomes one JSON line. A request the hook rejects never reaches the mock,
so it is never recorded.


## Testing

LeakGuard provides shared pytest fixtures for isolated PostgreSQL testing, encryption, and synthetic POC dataset access.

For setup instructions, local test execution, fixture usage, and CI integration, see the [Testing Guide](docs/testing.md).



## Development

```bash
pip install -e ".[dev]"            # core + pytest (LiteLLM tests are skipped)
pip install -e ".[dev,litellm]"    # + LiteLLM Proxy (what the CI test job installs)
pip install -e ".[dev,all]"        # + sentence-transformers/transformers (pulls in PyTorch)
pytest
```
