"""«interface» Repository[T]: the generic persistence port every aggregate repository extends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, TypeVar
from uuid import UUID

T = TypeVar("T")

QueryFilter = Mapping[str, Any]
"""Field name -> required value. Kept generic on purpose; each implementation maps it to SQL."""


class Repository(ABC, Generic[T]):
    """«interface» Repository[T]: CRUD on one aggregate root type."""

    @abstractmethod
    def get(self, id: UUID) -> T:
        """Return the aggregate with this id. Raises NotFoundError if it does not exist."""

    @abstractmethod
    def save(self, item: T) -> None:
        """Insert or update the whole aggregate in one transaction."""

    @abstractmethod
    def delete(self, id: UUID) -> None:
        """Delete the aggregate with this id."""

    @abstractmethod
    def query(self, filter: QueryFilter) -> list[T]:
        """Return every aggregate that matches the filter."""
