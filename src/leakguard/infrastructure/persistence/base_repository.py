"""BaseRepositoryImpl[T] (ADD 5.2.11)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar
from uuid import UUID

from leakguard.domain.common.repository import QueryFilter, Repository
from leakguard.infrastructure.security.crypto_service import CryptoService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepositoryImpl(Repository[T], Generic[T]):
    """Shared CRUD on SQLAlchemy.

    Encrypts the fields marked *encrypted* on save and decrypts them on load (NFR-01):
    decrypt(encrypt(x)) = x. One transaction per service call. Optimistic locking
    with a version column against conflicting updates (NFR-16).
    """

    def __init__(self, session: Session, crypto: CryptoService) -> None:
        self._session = session
        self._crypto = crypto

    def get(self, id: UUID) -> T:
        raise NotImplementedError

    def save(self, item: T) -> None:
        raise NotImplementedError

    def delete(self, id: UUID) -> None:
        raise NotImplementedError

    def query(self, filter: QueryFilter) -> list[T]:
        raise NotImplementedError
