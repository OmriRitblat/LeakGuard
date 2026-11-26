
"""ORM models for organizational secrets and their detection data."""

from uuid import UUID

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import (
    REAL,
    CheckConstraint,
    ForeignKey,
    LargeBinary,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from leakguard.infrastructure.persistence.orm_models.base import Base


class SecretRow(Base):
    """Database representation of an organizational secret."""

    __tablename__ = "secrets"

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'REMOVED')",
            name="ck_secrets_status",
        ),
        CheckConstraint(
            "pass_threshold >= 0 AND "
            "pass_threshold < block_threshold AND "
            "block_threshold <= 1",
            name="ck_secrets_thresholds",
        ),
        CheckConstraint(
            "ce_threshold BETWEEN 0 AND 1",
            name="ck_secrets_ce_threshold",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    code: Mapped[str] = mapped_column(
        Text, unique=True, nullable=False
    )

    name_enc: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )

    description_enc: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )

    pass_threshold: Mapped[float] = mapped_column(
        REAL, nullable=False
    )

    block_threshold: Mapped[float] = mapped_column(
        REAL, nullable=False
    )

    ce_threshold: Mapped[float] = mapped_column(
        REAL, nullable=False
    )

    status: Mapped[str] = mapped_column(
        Text, nullable=False
    )


class ExposurePolicyItemRow(Base):
    """An exposure policy item belonging to a secret."""

    __tablename__ = "exposure_policy_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    secret_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("secrets.id"),
        nullable=False,
    )

    item_type: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    text_enc: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )


class LabeledExampleRow(Base):
    """A labeled exposure or non-exposure example."""

    __tablename__ = "labeled_examples"

    __table_args__ = (
        CheckConstraint(
            "label IN ('EXPOSURE', 'NON_EXPOSURE')",
            name="ck_labeled_examples_label",
        ),
        CheckConstraint(
            "source IN ('ADMIN', 'GENERATED', 'VERIFIED')",
            name="ck_labeled_examples_source",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    secret_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("secrets.id"),
        nullable=False,
    )

    text_enc: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )

    label: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    source: Mapped[str] = mapped_column(
        Text, nullable=False
    )


class SecretVectorRow(Base):
    """Stored reference vector associated with a secret."""

    __tablename__ = "secret_vectors"

    __table_args__ = (
        CheckConstraint(
            "kind IN ('DESCRIPTION', 'POLICY_DETAIL', 'EXAMPLE')",
            name="ck_secret_vectors_kind",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    secret_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("secrets.id"),
        nullable=False,
    )

    kind: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    source_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    text_enc: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False
    )

    # Dimension will be fixed after the Bi-Encoder is selected.
    embedding: Mapped[list[float]] = mapped_column(
        VECTOR(),
        nullable=False,
    )
