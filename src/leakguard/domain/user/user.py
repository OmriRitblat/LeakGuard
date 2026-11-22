"""The User aggregate (ADD 5.2.8)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class User:
    """«aggregate root» User: a login identity.

    Invariant UniqueEmail: e-mails are unique (INV-04).
    password_hash is never the plain password (NFR-06).
    """

    id: UUID
    email: str
    password_hash: str


@dataclass
class Admin(User):
    """The single System Administrator.

    Invariant SingleAdmin: exactly one Admin exists (INV-01).
    Hint: one users table with a user_type column; a partial unique index on
    user_type = 'ADMIN' backs INV-01.
    """
