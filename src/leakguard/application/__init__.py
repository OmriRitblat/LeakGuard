"""Application layer: the five services. A service never holds another service.

Every method a logged-in person calls takes ``caller: Token``, already checked by
the API layer; admin-only methods require caller.is_admin (FR-25, INV-03).
"""
