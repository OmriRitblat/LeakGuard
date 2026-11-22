"""«interface» TokenIssuer (ADD 5.2.8)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from leakguard.domain.common.value_objects import Token
from leakguard.domain.user.user import User


class TokenIssuer(ABC):
    """Creates and checks signed tokens."""

    @abstractmethod
    def issue(self, user: User) -> Token:
        """Return a signed token for the user; is_admin is True only for the Admin."""

    @abstractmethod
    def verify(self, value: str) -> Token:
        """Turn a token string back into a Token.

        Post RoundTrip:  verify(issue(u).value).user_id = u.id.
        Post NotExpired: result.expires_at > now; an expired or altered token raises AuthenticationError.
        """
