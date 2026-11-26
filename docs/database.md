# Local PostgreSQL database – developer setup

This guide covers the **local database infrastructure** used by LeakGuard: PostgreSQL 16,
pgvector, SQLAlchemy ORM schema initialization, and integration tests.

**Scope:** This is a database-only Docker Compose setup for development. It is not the
full LiteLLM + LeakGuard deployment, and each developer runs an independent database.
The initial schema contains **10 tables** corresponding to the approved ERD.

## Prerequisites

- Docker Desktop with WSL 2 on Windows, or Docker Engine with Compose on Linux.
- Python **3.11** (the team's tested version), plus Git.
- A checked-out LeakGuard repository with `compose.yaml`, `.env.example`,
  `src/leakguard/infrastructure/persistence/init_db.py`, and the ORM modules.
- Run all commands below from the **repository root** (where `pyproject.toml` is).

## 1. Configure local credentials

The `.env.example` file is committed to Git. Copy it to `.env`, which is ignored by Git:

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**Linux/macOS shell:**

```bash
cp .env.example .env
```

Edit `.env` and configure the values:

```dotenv
POSTGRES_DB=leakguard
POSTGRES_USER=leakguard
POSTGRES_PASSWORD=<choose-a-unique-local-password>
POSTGRES_PORT=5432
```

Replace `<choose-a-unique-local-password>` with a strong password (without the
angle brackets). If port 5432 is occupied or blocked on the host, use
`POSTGRES_PORT=55432` (or another free port) instead. **Only the host port
changes; PostgreSQL still uses port 5432 inside Docker.**

Every developer chooses their own local password. Do **not** commit `.env`, paste
its contents into an issue/PR, or put a production secret in `.env.example`.

`POSTGRES_USER` is an initialization user with broad database privileges;
it is appropriate for this isolated local setup, **not** the production app
identity. Production credentials and permissions require separate hardening.

## 2. Install the Python project

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

**Linux/macOS shell:**

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

If `.venv` already exists, reuse it; do not recreate it. The commands install
SQLAlchemy, psycopg, pgvector's Python bindings, python-dotenv and pytest, without
the optional ML or LiteLLM stacks.

## 3. Start the database

```text
docker compose config --quiet
docker compose up -d db
docker compose ps
```

`docker compose ps` should show service `db` with status **healthy**.
The Compose service exposes PostgreSQL to the host on `127.0.0.1:${POSTGRES_PORT}`,
not to other network interfaces by default.

The first run downloads `pgvector/pgvector:0.8.7-pg16-trixie` and creates a
persistent named Docker volume. The pgvector extension is then enabled by the
Python initialization command below.

If startup fails, inspect the logs:

```text
docker compose logs --tail 50 db
```

## 4. Initialize the schema

From the repository root, with PostgreSQL running:

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m leakguard.infrastructure.persistence.init_db
```

**Linux/macOS:**

```bash
.venv/bin/python -m leakguard.infrastructure.persistence.init_db
```

The initializer enables `CREATE EXTENSION IF NOT EXISTS vector` and creates the
missing ORM tables. It is **safe to rerun for tables that already exist**, but
`SQLAlchemy create_all()` is **not** a migration system: it does not alter existing
tables to match later model changes. Schema updates will need explicit migrations
(e.g. Alembic) once the models evolve.

Verify the result:

```text
docker compose exec db psql -U leakguard -d leakguard -c "\dt"
docker compose exec db psql -U leakguard -d leakguard -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

The table list should contain:

- `users`, `admins`, `view_permissions`
- `secrets`, `exposure_policy_items`, `labeled_examples`, `secret_vectors`
- `inspection_records`, `findings`, `verification_cases`

The `secret_vectors.embedding` column is currently `VECTOR` **without a fixed
dimension**. The dimension and any similarity-search index are owned by the
Bi-Encoder/vector-search implementation and will be finalized with the team.
Do not put unrelated vectors of different dimensions into a common search index.

## 5. Run database integration tests

The database tests are opt-in for a normal local `pytest` run so that the
application test suite does not require PostgreSQL on every developer's machine.
They perform schema inspection and should not insert sensitive fixtures.

**Windows PowerShell:**

```powershell
$env:LEAKGUARD_RUN_DB_TESTS = "1"
try {
    .\.venv\Scripts\python.exe -m pytest tests/integration/test_database_schema.py -v
} finally {
    Remove-Item Env:\LEAKGUARD_RUN_DB_TESTS -ErrorAction SilentlyContinue
}
```

**Linux/macOS shell:**

```bash
LEAKGUARD_RUN_DB_TESTS=1 .venv/bin/python -m pytest tests/integration/test_database_schema.py -v
```

The current integration suite checks the presence of 10 tables, primary keys,
selected foreign keys and constraints, the pgvector extension, and columns/types
against the ERD. Do not assume that these tests validate application behavior,
correct encryption, or database migrations.

A separate GitHub Actions database job can run these tests automatically against
an ephemeral PostgreSQL instance with pgvector; see `.github/workflows/ci.yml`.

## 6. Connect using DBeaver (optional)

Create a **PostgreSQL** connection with:

| Field | Value |
| --- | --- |
| Host | `127.0.0.1` |
| Port | `POSTGRES_PORT` from your `.env` (`5432` or `55432`) |
| Database | `leakguard` |
| Username | `leakguard` |
| Password | Your **local** `POSTGRES_PASSWORD` |

Click **Test Connection**, then browse **Schemas → public → Tables**.
DBeaver is a client; PostgreSQL stays inside Docker.

## 7. Normal use and troubleshooting

- Restart a stopped database: `docker compose up -d db`
- Stop without deleting stored data: `docker compose stop db`
- Stop/remove the service container and network, **keeping** the named volume:
  `docker compose down`
- **Danger:** `docker compose down -v` removes the named volume and destroys the
  locally stored database contents. Do not run it unless you deliberately want a
  fresh database and have backups of anything you need.
- **Port 5432 unavailable (Windows bind error):** change `POSTGRES_PORT` in `.env`
  to `55432`, then rerun `docker compose up -d db`.
- **Authentication failures after editing the password:** PostgreSQL sets the
  initial database password when the data directory is first created. Merely
  editing `.env` later **does not change** the existing PostgreSQL user's password.
  Change it intentionally via SQL if needed; do not reset a populated volume.
- **Cannot import LeakGuard modules:** run editable installation from the repo
  root and check that ORM files are under
  `src/leakguard/infrastructure/persistence/orm_models/`.
- **Python connects on the host:** the default `POSTGRES_HOST` is `127.0.0.1` and
  `POSTGRES_PORT` is the published host port. If the Python application later runs
  inside another Compose container, use `POSTGRES_HOST=db` and port `5432`
  inside the Compose network instead.
- Run `docker compose config --quiet` rather than printing resolved Compose
  configuration, which may include expanded environment credentials.

## 8. Security and current limitations

- This setup is for **local development and synthetic POC data**. It has no
  production backup/restore, migration, monitoring, least-privilege-user or
  key-management solution yet.
- A Docker named volume **provides persistence, not guaranteed encryption**.
  Check filesystem/disk encryption separately. PostgreSQL itself handles
  vector data in readable form during queries.
- Sensitive text columns (`*_enc`) are typed as `BYTEA`, but **the schema does not
  encrypt their contents**. The application must implement and use
  `CryptoService` (AES-256-GCM, a fresh random nonce per encryption) before
  writing sensitive text.