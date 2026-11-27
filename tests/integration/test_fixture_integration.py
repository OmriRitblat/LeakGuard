
"""Integration tests for shared POC testing fixtures."""

from sqlalchemy import select

from leakguard.infrastructure.persistence.orm_models.secret_models import (
    SecretRow,
)


def test_train_data_encrypted_database_roundtrip(
    db_session,
    train_data,
    crypto_service,
):
    secret = train_data["ss001_train"]["secret"]
    test_code = f"TEST-{secret['code']}"

    row = SecretRow(
        code=test_code,
        name_enc=crypto_service.encrypt(secret["name"]),
        description_enc=crypto_service.encrypt(secret["description"]),
        # Test-only values for required database columns.
        pass_threshold=0.2,
        block_threshold=0.8,
        ce_threshold=0.5,
        status="REMOVED",
    )

    db_session.add(row)
    db_session.commit()
    db_session.expunge_all()

    stored = db_session.scalar(
        select(SecretRow).where(SecretRow.code == test_code)
    )

    assert stored is not None
    assert stored.name_enc != secret["name"].encode("utf-8")
    assert stored.description_enc != secret["description"].encode("utf-8")

    assert crypto_service.decrypt(stored.name_enc) == secret["name"]
    assert (
        crypto_service.decrypt(stored.description_enc)
        == secret["description"]
    )
