"""SecretAccessService (ADD 5.2.7)."""

from __future__ import annotations

from uuid import UUID

from leakguard.domain.common.value_objects import Token
from leakguard.domain.secret.repository import SecretRepository
from leakguard.domain.secret.secret import Secret


class SecretAccessService:
    """UC-04, UC-05: who may see a secret.

    Holds only SecretRepository, because permissions live inside the Secret aggregate.
    """

    def __init__(self, secrets: SecretRepository) -> None:
        self._secrets = secrets

    def view(self, caller: Token, secret_id: UUID) -> Secret:
        """Show a secret's details to the admin or a permitted user (FR-24, UC-05).

        Pre  Active:  the secret is ACTIVE (UC-05 A2).
        Pre  Allowed: caller.is_admin or the secret has a permission for caller.user_id (UC-05 A1).
        Post ReadOnly: no state changes.
        Returns the name and description only, never the examples (NFR-04).
        A missing and a forbidden secret raise the same NotAvailableError (NFR-19).
        """
        raise NotImplementedError

    def set_permission(self, caller: Token, secret_id: UUID, user_id: UUID, granted: bool) -> None:
        """Grant or revoke a user's viewing permission (FR-15, UC-04).

        Pre  Admin: caller.is_admin (INV-03); the secret is ACTIVE; the user exists.
        Pre  Changes: the current state differs from ``granted``.
        Post Applied: the secret has a permission for user_id exactly when granted.
        """
        raise NotImplementedError
