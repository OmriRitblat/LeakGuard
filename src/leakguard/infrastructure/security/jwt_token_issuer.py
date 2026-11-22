"""JwtTokenIssuer (ADD 5.2.11)."""

from __future__ import annotations

from datetime import timedelta

from leakguard.domain.common.value_objects import Token
from leakguard.domain.ports.token_issuer import TokenIssuer
from leakguard.domain.user.user import User


class JwtTokenIssuer(TokenIssuer):
    """TokenIssuer with signed JWTs.

    Fields (not in diagram v11, from the ADD hints):
      signing_key: comes from the environment, never the database.
      lifetime: short, for example one working day, because the token carries
        is_admin and a removed user keeps access until it expires.
    """

    def __init__(self, signing_key: str, lifetime: timedelta) -> None:
        self._signing_key = signing_key
        self._lifetime = lifetime

    def issue(self, user: User) -> Token:
        raise NotImplementedError

    def verify(self, value: str) -> Token:
        """An expired or altered token raises AuthenticationError."""
        raise NotImplementedError
