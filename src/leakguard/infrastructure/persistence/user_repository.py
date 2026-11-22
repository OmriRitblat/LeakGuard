"""UserRepositoryImpl."""

from __future__ import annotations

from leakguard.domain.user.repository import UserRepository
from leakguard.domain.user.user import Admin, User
from leakguard.infrastructure.persistence.base_repository import BaseRepositoryImpl


class UserRepositoryImpl(BaseRepositoryImpl[User], UserRepository):
    """UserRepository on SQLAlchemy (one users table with a user_type column)."""

    def find_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    def get_admin(self) -> Admin:
        raise NotImplementedError
