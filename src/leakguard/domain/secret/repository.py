"""«interface» SecretRepository (ADD 5.2.5)."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from uuid import UUID

from leakguard.domain.common.repository import Repository
from leakguard.domain.inspection.snapshot import SecretSnapshot
from leakguard.domain.secret.secret import LabeledExample, Secret


class SecretRepository(Repository[Secret]):
    """Saves and loads the whole Secret aggregate and builds the snapshot of ACTIVE secrets."""

    @abstractmethod
    def list_active(self) -> list[Secret]:
        """Return every secret with status ACTIVE."""

    @abstractmethod
    def get_snapshot(self) -> SecretSnapshot:
        """Return the current immutable snapshot of the ACTIVE secrets (INV-05).

        Post: result.rules' secret ids = list_active() ids.
        Hint: with several worker processes (Alpha), keep the version number in the
        database and rebuild when it changes.
        """

    @abstractmethod
    def revoke_user(self, user_id: UUID) -> None:
        """Remove every ViewPermission of this user from every secret (FR-27).

        Post: no secret holds a permission with this user_id.
        Changes several aggregates in one transaction (a deliberate exception).
        """

    @abstractmethod
    def add_examples(self, secret_id: UUID, examples: Sequence[LabeledExample]) -> None:
        """Store new examples of a secret.

        Post: the secret's example count grows by len(examples).
        """

    @abstractmethod
    def list_examples(self, secret_id: UUID) -> list[LabeledExample]:
        """Return the secret's examples (loaded on demand)."""
