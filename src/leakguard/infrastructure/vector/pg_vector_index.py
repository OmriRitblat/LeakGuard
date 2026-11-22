"""PgVectorIndex (ADD 5.2.11)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from leakguard.domain.inspection.match import Match, MatchKind
from leakguard.domain.ports.vector_index import Vector, VectorIndex
from leakguard.infrastructure.security.crypto_service import CryptoService

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class PgVectorIndex(VectorIndex):
    """VectorIndex on pgvector (PC-05), in its own table: (ref_id, secret_id, kind, text, vector).

    The text is stored encrypted and decrypted before the Match is returned. The
    vector itself cannot be encrypted (see the ARD gap on NFR-01).

    Fields (not in diagram v11): session, crypto, and max_results, the LIMIT used
    as a safety cap on search.
    """

    def __init__(self, session: Session, crypto: CryptoService, max_results: int) -> None:
        self._session = session
        self._crypto = crypto
        self._max_results = max_results

    def search(self, vector: Vector, min_sim: float) -> list[Match]:
        raise NotImplementedError

    def upsert(self, ref_id: UUID, secret_id: UUID, kind: MatchKind, text: str, vector: Vector) -> None:
        raise NotImplementedError

    def remove_secret(self, secret_id: UUID) -> None:
        raise NotImplementedError

    def contains(self, ref_id: UUID) -> bool:
        raise NotImplementedError
