"""SecretRepositoryImpl."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from leakguard.domain.inspection.snapshot import SecretSnapshot
from leakguard.domain.secret.repository import SecretRepository
from leakguard.domain.secret.secret import LabeledExample, Secret
from leakguard.infrastructure.persistence.base_repository import BaseRepositoryImpl


class SecretRepositoryImpl(BaseRepositoryImpl[Secret], SecretRepository):
    """SecretRepository on SQLAlchemy. Removal is a soft delete (status = REMOVED)."""

    def list_active(self) -> list[Secret]:
        raise NotImplementedError

    def get_snapshot(self) -> SecretSnapshot:
        raise NotImplementedError

    def revoke_user(self, user_id: UUID) -> None:
        raise NotImplementedError

    def add_examples(self, secret_id: UUID, examples: Sequence[LabeledExample]) -> None:
        raise NotImplementedError

    def list_examples(self, secret_id: UUID) -> list[LabeledExample]:
        raise NotImplementedError
