"""Domain errors named in the ADD (5.2). Not drawn in class diagram v11."""

from __future__ import annotations


class LeakGuardError(Exception):
    """Base class of every LeakGuard domain error."""


class UnknownUserError(LeakGuardError):
    """The request's user_ref matches no user (UC-02 step 3). The hook treats it as a failed inspection."""


class AuthenticationError(LeakGuardError):
    """Login failed, or a token is expired or altered (UC-01 A1).

    One message covers an unknown e-mail and a wrong password.
    """


class PermissionDeniedError(LeakGuardError):
    """The caller is not the System Administrator where one is required (FR-25, INV-03)."""


class NotAvailableError(LeakGuardError):
    """A secret is missing, removed or forbidden to the caller (UC-05 A1, A2).

    The same error for all three cases, so users cannot probe secret identifiers (NFR-19).
    """


class NotFoundError(LeakGuardError):
    """An aggregate with the given id does not exist."""


class InvalidStateError(LeakGuardError):
    """The object is not in the state the operation needs (e.g. a case that is not PENDING)."""


class ValidationError(LeakGuardError):
    """An input breaks a pre-condition (e.g. malformed e-mail, period.start > period.end)."""
