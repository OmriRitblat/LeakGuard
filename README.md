# LeakGuard

Semantic DLP guardrail for LiteLLM Proxy (BGU Software Engineering final project).

**Status: code skeleton.** Packages, classes, interfaces, fields and method signatures
from `LeakGuard_class_diagram_v11` and the ADD (5.2 Class Description). Method bodies
raise `NotImplementedError`. Each docstring carries the ADD's pre/post-conditions.

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
  infrastructure/              INFRASTRUCTURE LAYER
    litellm/                   LeakGuardGuardrail (LiteLLM hook), FailurePolicy,
                               InspectionClient, InProcessInspectionClient (POC),
                               HttpInspectionClient (Alpha)
    persistence/               BaseRepositoryImpl[T] + 4 repository implementations
    security/                  CryptoService, Argon2PasswordHasher, JwtTokenIssuer
    vector/                    PgVectorIndex
    models/                    SentenceTransformerBiEncoder, HfCrossEncoderModel, HfLocalLlm
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
  `model_name` on the three model adapters.
- `UserRepository.find_by_email` returns `User | None`.

## Not yet in the skeleton

FastAPI routers (the API layer that checks `caller`), SQLAlchemy ORM models (see
`LeakGuard_ERD.drawio`), configuration/wiring, and the management UI.

## Development

```bash
pip install -e ".[dev]"            # core + pytest (what CI installs)
pip install -e ".[dev,litellm]"    # + LiteLLM, for the guardrail hook
pip install -e ".[dev,all]"        # + sentence-transformers/transformers (pulls in PyTorch)
pytest
```
