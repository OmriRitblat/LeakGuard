
"""Tests for the isolated PostgreSQL test database."""
import pytest
from sqlalchemy import select, text

from leakguard.infrastructure.persistence.orm_models.user_models import UserRow


def test_uses_isolated_database(test_db_engine):
    with test_db_engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

    assert database_name == "leakguard_test"


def test_db_session_supports_commit(db_session):
    user = UserRow(
        email="test-session@example.test",
        password_hash="test-only-placeholder",
    )

    db_session.add(user)
    db_session.commit()

    stored_user = db_session.scalar(
        select(UserRow).where(
            UserRow.email == "test-session@example.test"
        )
    )

    assert stored_user is not None
    assert stored_user.email == user.email


@pytest.mark.parametrize("attempt", [1, 2])
def test_db_session_isolation(db_session, test_db_engine, attempt):
    email = "isolation-test@example.test"

    existing_user = db_session.scalar(
        select(UserRow).where(UserRow.email == email)
    )
    assert existing_user is None

    user = UserRow(
        email=email,
        password_hash="test-only-placeholder",
    )

    db_session.add(user)
    db_session.commit()

    stored_user = db_session.scalar(
        select(UserRow).where(UserRow.email == email)
    )
    assert stored_user is not None

    with test_db_engine.connect() as other_connection:
        visible_count = other_connection.execute(
            text("SELECT COUNT(*) FROM users WHERE email = :email"),
            {"email": email},
        ).scalar_one()

    assert visible_count == 0


def test_crypto_service_fixture(crypto_service):
    plaintext = "Confidential organizational information"

    encrypted = crypto_service.encrypt(plaintext)
    decrypted = crypto_service.decrypt(encrypted)

    assert encrypted != plaintext.encode("utf-8")
    assert decrypted == plaintext
