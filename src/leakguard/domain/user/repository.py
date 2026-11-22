"""«interface» UserRepository (ADD 5.2.8)."""

from __future__ import annotations

from abc import abstractmethod

from leakguard.domain.common.repository import Repository
from leakguard.domain.user.user import Admin, User


class UserRepository(Repository[User]):
    """Persistence port of the User aggregate."""

    @abstractmethod
    def find_by_email(self, email: str) -> User | None:
        """Return the user with this e-mail, or None (UC-02 step 3, UC-01)."""

    @abstractmethod
    def get_admin(self) -> Admin:
        """Return the single System Administrator (INV-01)."""
