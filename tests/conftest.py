
"""Shared pytest fixtures for LeakGuard tests."""

import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from leakguard.infrastructure.persistence.orm_models import Base
from leakguard.infrastructure.security.crypto_service import CryptoService
from tests.dataset_loader import EVAL_DIR, TRAIN_DIR, load_json


@pytest.fixture(scope="session")
def test_db_engine():
    """Provide a SQLAlchemy engine for the isolated test database."""
    if os.getenv("LEAKGUARD_RUN_TEST_DB") != "1":
        pytest.skip("Isolated database tests are not enabled")

    load_dotenv(".env", override=False)

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username="leakguard_test",
        password=os.getenv(
            "POSTGRES_TEST_PASSWORD",
            "local_test_only_password",
        ),
        host="127.0.0.1",
        port=int(os.getenv("POSTGRES_TEST_PORT", "55433")),
        database="leakguard_test",
    )

    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        with engine.connect() as connection:
            database_name, username = connection.execute(
                text("SELECT current_database(), current_user")
            ).one()

            if (
                database_name != "leakguard_test"
                or username != "leakguard_test"
            ):
                raise RuntimeError(
                    "Refusing to initialize a non-test database"
                )

        with engine.begin() as connection:
            connection.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )
            Base.metadata.create_all(bind=connection)

        yield engine

    finally:
        engine.dispose()


@pytest.fixture
def db_session(test_db_engine):
    """Provide an isolated database session for each test."""
    with test_db_engine.connect() as connection:
        transaction = connection.begin()

        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def crypto_service() -> CryptoService:
    """Provide a CryptoService with a temporary test encryption key."""
    return CryptoService(os.urandom(32))


@pytest.fixture
def train_data():
    """Provide the synthetic TRAIN datasets to tests."""
    files = sorted(TRAIN_DIR.glob("*_train.json"))

    if not files:
        raise FileNotFoundError("No TRAIN dataset files found")

    return {path.stem: load_json(path) for path in files}


@pytest.fixture
def eval_data():
    """Provide the synthetic EVAL datasets to tests."""
    files = sorted(EVAL_DIR.glob("*_eval.json"))

    if not files:
        raise FileNotFoundError("No EVAL dataset files found")

    return {path.stem: load_json(path) for path in files}
