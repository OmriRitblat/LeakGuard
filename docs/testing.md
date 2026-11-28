# Testing Guide

This guide explains how to use LeakGuard's shared pytest fixtures, isolated PostgreSQL test database, and synthetic POC datasets. Run the commands from the repository root (the directory containing `pyproject.toml`).

For database installation and development setup, see [Database Setup](database.md). For the dataset format and labeling conventions, see the [POC Dataset README](../datasets/leakguard_poc/README.md).

## 1. Prerequisites

- Python 3.11 with the project's development dependencies installed:

  ```bash
  python -m pip install -e ".[dev]"
  ```

- Docker Desktop or Docker Engine with Compose, **only for database-dependent tests**.
- The repository's synthetic TRAIN and EVAL JSON files under `datasets/leakguard_poc/`.

Unit tests and dataset validation tests do not require Docker, PostgreSQL, or a real encryption key.

## 2. Run tests without PostgreSQL

From the project root:

```bash
python -m pytest -v
```

This runs unit tests, dataset loading tests, and dataset validation tests. Database-dependent tests are skipped unless their corresponding environment flags are enabled.

To run only the dataset-related tests:

```bash
python -m pytest tests/unit/test_dataset_loader.py tests/unit/test_dataset_validation.py -v
```

## 3. Isolated PostgreSQL test database

The test suite uses a separate Docker Compose service, `db_test`, rather than the normal development service, `db`.

| | Development | Isolated tests |
| --- | --- | --- |
| Docker Compose service | `db` | `db_test` |
| Database | `leakguard` | `leakguard_test` |
| Database user | `leakguard` | `leakguard_test` |
| Host port | `POSTGRES_PORT` (e.g., `55432`) | `POSTGRES_TEST_PORT` (default `55433`) |
| Storage | Persistent Docker volume | Temporary `tmpfs` |

`db_test` belongs to the `test` Compose profile, so normal startup of `db` does not start it. Explicitly starting the named service does not require enabling the profile separately.

Start the isolated database:

```bash
docker compose up -d db_test
docker compose ps db_test
```

Wait until `db_test` reports `healthy`.

### Windows (PowerShell)

```powershell
$env:LEAKGUARD_RUN_TEST_DB = "1"
try {
    .\.venv\Scripts\python.exe -m pytest tests/integration/test_test_database.py tests/integration/test_fixture_integration.py -v
} finally {
    Remove-Item Env:\LEAKGUARD_RUN_TEST_DB -ErrorAction SilentlyContinue
}
```

### Linux / macOS

```bash
LEAKGUARD_RUN_TEST_DB=1 .venv/bin/python -m pytest \
  tests/integration/test_test_database.py \
  tests/integration/test_fixture_integration.py -v
```

The `LEAKGUARD_RUN_TEST_DB=1` flag enables tests that use the isolated database. The test fixtures connect to `leakguard_test`, verify the database name and user, initialize the `pgvector` extension and ORM schema, and manage per-test transactions. They must **never** reset the development database.

The test service's credentials are intended **only for local, isolated testing**. Do not reuse them for production or a shared database. If the default test port is unavailable, configure `POSTGRES_TEST_PORT` for both Docker Compose and the local test process.

## 4. Shared pytest fixtures

The shared fixtures are declared in `tests/conftest.py`. pytest injects them by name when a test function requests them as parameters.

| Fixture | Provides | Database required? |
| --- | --- | --- |
| `test_db_engine` | SQLAlchemy Engine connected to the isolated `leakguard_test` database, with the schema initialized | Yes |
| `db_session` | SQLAlchemy Session scoped to one test, with an outer transaction and rollback on teardown | Yes |
| `crypto_service` | `CryptoService` with a new random 32-byte test key | No |
| `train_data` | Dictionary of TRAIN JSON objects, keyed by filename stem | No |
| `eval_data` | Dictionary of EVAL JSON objects, keyed by filename stem | No |

The Engine fixture is session-scoped; the database Session fixture is function-scoped. `db_session` uses SQLAlchemy SAVEPOINT handling so code under test can call `session.commit()` while its changes remain inside the outer transaction. That transaction is rolled back after the test.

**Important limitation:** This rollback applies to operations using the fixture-provided connection/Session. A component that creates an independent connection or Engine is not automatically isolated by this fixture. Inject the provided Session into the code under test whenever possible.

`crypto_service` uses a temporary test key, **not** the developer's `LEAKGUARD_ENCRYPTION_KEY` in `.env`. No manual key-generation step is needed for these tests.

### Example: accessing the datasets

```python
def test_poc_data_is_available(train_data, eval_data):
    secret = train_data["ss001_train"]["secret"]
    cases = eval_data["ss001_eval"]["cases"]

    assert secret["code"] == "SS-001"
    assert cases
```

### Example: database and encryption fixtures

```python
from sqlalchemy import text


def test_database_and_crypto_fixtures(db_session, crypto_service):
    database_name = db_session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    encrypted = crypto_service.encrypt("Synthetic test content")

    assert database_name == "leakguard_test"
    assert crypto_service.decrypt(encrypted) == "Synthetic test content"
```

For a working database/JSON/encryption integration example, see `tests/integration/test_fixture_integration.py`.

## 5. POC TRAIN and EVAL datasets

Dataset root: `datasets/leakguard_poc/`.

- TRAIN files are stored under `data/` (`ss001_train.json`, `ss002_train.json`, `ss003_train.json`). `train_data` exposes them as `train_data["ss001_train"]`, etc.
- EVAL files are stored under `tests/fixtures/` (`ss001_eval.json`, `ss002_eval.json`, `ss003_eval.json`, `multi_secret_eval.json`, `pii_eval.json`). `eval_data` exposes them as `eval_data["ss001_eval"]`, etc.

The fixtures read JSON and return Python dictionaries. **They do not seed PostgreSQL, construct domain objects, calculate embeddings, calibrate thresholds, or execute the inspection pipeline.**

The dataset validation tests check required fields, supported labels and decisions, unique identifiers, and relevant references to TRAIN secret codes. They validate dataset structure; they **do not** establish that a model's predictions or the annotations themselves are semantically correct.


## 6. GitHub Actions

The `.github/workflows/ci.yml` workflow runs on pull requests and pushes to `main`:

- The `test` job runs the regular pytest suite, including the dataset loading and validation tests, without requiring a database.
- The `database` job runs PostgreSQL schema integration tests and the new isolated database-fixture tests. Its test database uses a separate temporary PostgreSQL service with `LEAKGUARD_RUN_TEST_DB=1`.

The existing schema tests use a **different flag**, `LEAKGUARD_RUN_DB_TESTS=1`, and connect through the normal database configuration (`create_db_engine()`). They should not be confused with tests using the isolated `db_session` fixture. The two test paths must use the appropriate database configuration.

## 7. LiteLLM proxy and mock LLM tests

These tests need the `litellm` extra (`pip install -e ".[dev,litellm]"`, as in CI) and are
skipped without it. They start a real LiteLLM proxy as a subprocess and send HTTP requests to
it, so they cover client -> LiteLLM -> hook -> mock LLM:

- `tests/integration/test_litellm_proxy.py` uses `config/litellm.yaml` with the real LeakGuard hook.
- `tests/integration/test_mock_llm_flow.py` uses `tests/utils/litellm_test.yaml`, where test
  doubles of the hook (`tests/utils/litellm_doubles.py`: `spy`, `reject`, `replace`) are chosen
  per request with `"guardrails": ["<name>"]`.

There is no separate LeakGuard configuration for tests: they read `config/leakguard.yaml` and
override single values through environment variables. `tests/utils/litellm_proxy.py` starts the
proxy with `start_proxy(config, work_dir)` on a free port, a random master key and mock LLM
recording on (`LEAKGUARD_MOCK_LLM__RECORD_FILE` points to a temporary file). The hook doubles
and the mock LLM write to the same record file, so a test can check what reached the hook, what
reached the LLM and in which order:

```python
from leakguard.infrastructure.litellm.mock_llm_provider import RECEIVED_EVENT, read_events

def test_example(proxy, record):          # record = proxy.clear_record(), emptied per test
    ...                                   # send a request to proxy.base_url with proxy.auth
    assert [e["event"] for e in read_events(record)] == ["hook_approved", RECEIVED_EVENT]
```

## 8. Current scope and limitations

This infrastructure supports repeatable dataset validation, isolated database testing, and test helpers shared across the team. It does **not** yet provide:

- Full TRAIN-to-PostgreSQL seeding for a complete POC reference corpus.
- Embedding creation, vector indexing, or threshold calibration.
- End-to-end EVAL execution against the detection pipeline.
- Application-startup wiring for the production `CryptoService`.

These integrations will be implemented separately as the corresponding application components become available.
