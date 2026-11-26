
"""ORM models for inspection records, findings, and verification cases."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    REAL,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from leakguard.infrastructure.persistence.orm_models.base import Base


class InspectionRecordRow(Base):
    """Database record of an inspected request."""

    __tablename__ = "inspection_records"

    __table_args__ = (
        CheckConstraint(
            "decision IN ('ALLOW', 'REDACT', 'BLOCK')",
            name="ck_inspection_records_decision",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_inspection_records_latency",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    decision: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    snapshot_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )


class FindingRow(Base):
    """A finding produced during an inspection."""

    __tablename__ = "findings"

    __table_args__ = (
        CheckConstraint(
            "type IN ('PII', 'SECRET_EXPOSURE')",
            name="ck_findings_type",
        ),
        CheckConstraint(
            "(type = 'PII' AND secret_id IS NULL) OR "
            "(type = 'SECRET_EXPOSURE' AND secret_id IS NOT NULL)",
            name="ck_findings_secret_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    inspection_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("inspection_records.id"),
        nullable=False,
    )

    secret_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("secrets.id"),
        nullable=True,
    )

    type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    score: Mapped[float | None] = mapped_column(
        REAL,
        nullable=True,
    )

    stage: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )


class VerificationCaseRow(Base):
    """A case awaiting or having completed administrator verification."""

    __tablename__ = "verification_cases"

    __table_args__ = (
        CheckConstraint(
            "recommended_label IN ('EXPOSURE', 'NON_EXPOSURE')",
            name="ck_verification_cases_recommended_label",
        ),
        CheckConstraint(
            "verified_label IS NULL OR "
            "verified_label IN ('EXPOSURE', 'NON_EXPOSURE')",
            name="ck_verification_cases_verified_label",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'VERIFIED')",
            name="ck_verification_cases_status",
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

    content_enc: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    recommended_label: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    verified_label: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=text("'PENDING'"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
