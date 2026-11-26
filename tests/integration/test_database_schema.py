
"""Integration tests for the PostgreSQL database schema."""

import os

import pytest
from sqlalchemy import inspect, text

from leakguard.infrastructure.persistence.database import create_db_engine

EXPECTED_TABLES = {
    "users",
    "admins",
    "secrets",
    "exposure_policy_items",
    "labeled_examples",
    "secret_vectors",
    "view_permissions",
    "verification_cases",
    "inspection_records",
    "findings",
}


@pytest.fixture(scope="module")
def engine():
    """Connect to the development database only when explicitly enabled."""
    if os.getenv("LEAKGUARD_RUN_DB_TESTS") != "1":
        pytest.skip("Database integration tests are not enabled")

    db_engine = create_db_engine()
    try:
        yield db_engine
    finally:
        db_engine.dispose()


def test_all_tables_exist(engine):
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names(schema="public"))

    assert actual_tables == EXPECTED_TABLES


def test_primary_keys(engine):
    inspector = inspect(engine)

    for table_name in EXPECTED_TABLES:
        primary_key = inspector.get_pk_constraint(table_name)
        assert primary_key["constrained_columns"]

    permissions_pk = inspector.get_pk_constraint(
        "view_permissions"
    )
    assert set(permissions_pk["constrained_columns"]) == {
        "secret_id",
        "user_id",
    }


def test_secret_foreign_keys(engine):
    inspector = inspect(engine)

    for table_name in (
        "exposure_policy_items",
        "labeled_examples",
        "secret_vectors",
    ):
        foreign_keys = inspector.get_foreign_keys(table_name)

        assert any(
            fk["referred_table"] == "secrets"
            and fk["constrained_columns"] == ["secret_id"]
            for fk in foreign_keys
        )


def test_vector_extension_enabled(engine):
    with engine.connect() as connection:
        installed = connection.execute(
            text(
                "SELECT EXISTS ("
                "SELECT 1 FROM pg_extension "
                "WHERE extname = 'vector'"
                ")"
            )
        ).scalar_one()

    assert installed


def test_secret_constraints(engine):
    inspector = inspect(engine)
    constraints = inspector.get_check_constraints("secrets")
    names = {constraint["name"] for constraint in constraints}

    assert {
        "ck_secrets_status",
        "ck_secrets_thresholds",
        "ck_secrets_ce_threshold",
    }.issubset(names)


def test_columns_match_erd(engine):
    """Verify that PostgreSQL columns and types match the approved ERD."""

    expected = {
        "users": {
            "id": "uuid",
            "email": "text",
            "password_hash": "text",
        },
        "admins": {
            "user_id": "uuid",
        },
        "secrets": {
            "id": "uuid",
            "code": "text",
            "name_enc": "bytea",
            "description_enc": "bytea",
            "pass_threshold": "float4",
            "block_threshold": "float4",
            "ce_threshold": "float4",
            "status": "text",
        },
        "exposure_policy_items": {
            "id": "uuid",
            "secret_id": "uuid",
            "item_type": "text",
            "text_enc": "bytea",
        },
        "labeled_examples": {
            "id": "uuid",
            "secret_id": "uuid",
            "text_enc": "bytea",
            "label": "text",
            "source": "text",
        },
        "secret_vectors": {
            "id": "uuid",
            "secret_id": "uuid",
            "kind": "text",
            "source_id": "uuid",
            "text_enc": "bytea",
            "embedding": "vector",
        },
        "view_permissions": {
            "secret_id": "uuid",
            "user_id": "uuid",
            "granted_at": "timestamptz",
        },
        "verification_cases": {
            "id": "uuid",
            "secret_id": "uuid",
            "content_enc": "bytea",
            "recommended_label": "text",
            "verified_label": "text",
            "status": "text",
            "created_at": "timestamptz",
        },
        "inspection_records": {
            "id": "uuid",
            "user_id": "uuid",
            "created_at": "timestamptz",
            "decision": "text",
            "snapshot_version": "int4",
            "latency_ms": "int4",
        },
        "findings": {
            "id": "uuid",
            "inspection_record_id": "uuid",
            "secret_id": "uuid",
            "type": "text",
            "score": "float4",
            "stage": "text",
        },
    }

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT table_name, column_name, udt_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
            """)
        ).mappings()

        actual = {table: {} for table in expected}

        for row in rows:
            table_name = row["table_name"]
            if table_name in actual:
                actual[table_name][row["column_name"]] = row["udt_name"]

    assert actual == expected