"""UserService (ADD 5.2.8)."""

from __future__ import annotations

from uuid import UUID

from leakguard.domain.common.value_objects import Token
from leakguard.domain.ports.password_hasher import PasswordHasher
from leakguard.domain.ports.token_issuer import TokenIssuer
from leakguard.domain.secret.repository import SecretRepository
from leakguard.domain.user.repository import UserRepository
from leakguard.domain.user.user import User


class UserService:
    """UC-01, UC-09, UC-10, and turning a token string back into a Token."""

    def __init__(
        self,
        users: UserRepository,
        secrets: SecretRepository,
        hasher: PasswordHasher,
        tokens: TokenIssuer,
    ) -> None:
        self._users = users
        self._secrets = secrets
        self._hasher = hasher
        self._tokens = tokens

    def login(self, email: str, password: str) -> Token:
        """Log a user in (UC-01).

        Post on success, result = tokens.issue(user), with user_id = user.id and is_admin set.
        On failure no token is issued, and one AuthenticationError covers an unknown
        e-mail and a wrong password (UC-01 A1).
        """
        raise NotImplementedError

    def verify_token(self, value: str) -> Token:
        """Return the Token if its signature is valid and it has not expired; else AuthenticationError."""
        raise NotImplementedError

    def register(self, caller: Token, email: str, password: str) -> User:
        """Register a new user (UC-09).

        Pre  caller.is_admin; e-mail well formed and not in use (UC-09 A1, A2).
        Post a new User with password_hash = hasher.hash(password) <> password (NFR-06).
        """
        raise NotImplementedError

    def remove(self, caller: Token, user_id: UUID) -> None:
        """Remove a user (UC-10).

        Pre  caller.is_admin; the user exists (UC-10 A1); the user is not the Admin (UC-10 A2).
        Post the user is deleted and secrets.revoke_user(user_id) ran in the same
             transaction (FR-27). Nothing changes on failure (UC-10 A3).
        """
        raise NotImplementedError
