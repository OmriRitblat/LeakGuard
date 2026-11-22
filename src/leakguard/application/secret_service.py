"""SecretService (ADD 5.2.6)."""

from __future__ import annotations

from uuid import UUID

from leakguard.domain.common.enums import Label
from leakguard.domain.common.value_objects import Token
from leakguard.domain.ports.bi_encoder import BiEncoder
from leakguard.domain.ports.local_llm import LocalLlm
from leakguard.domain.ports.vector_index import VectorIndex
from leakguard.domain.secret.repository import SecretRepository
from leakguard.domain.secret.secret import Secret, SecretDraft
from leakguard.domain.verification.repository import VerificationCaseRepository
from leakguard.domain.verification.verification_case import VerificationCase


class SecretService:
    """UC-03, UC-06, UC-07: the life of a secret and its detection data.

    Creates a secret and prepares it for detection, removes a secret, and runs the
    verification queue, learning from each verified case. Viewing and permissions
    are in SecretAccessService.
    """

    def __init__(
        self,
        secrets: SecretRepository,
        cases: VerificationCaseRepository,
        llm: LocalLlm,
        bi_encoder: BiEncoder,
        index: VectorIndex,
    ) -> None:
        self._secrets = secrets
        self._cases = cases
        self._llm = llm
        self._bi_encoder = bi_encoder
        self._index = index

    def create(self, caller: Token, draft: SecretDraft) -> Secret:
        """Create a secret and make it detectable (UC-03).

        Pre  Admin: caller.is_admin (INV-03).
        Pre  name and description not empty.
        Pre  BothLabels: at least one EXPOSURE and one NON_EXPOSURE example.
        Post Active: result.status = ACTIVE with a new id, and the next snapshot includes it.
        Post the draft's examples are stored with source = ADMIN.
        Post Indexed: _index_secret and _calibrate_thresholds ran.
        On failure nothing is saved (UC-03 A2).
        Then starts _generate_examples in the background (FR-16).
        """
        raise NotImplementedError

    def remove(self, caller: Token, secret_id: UUID) -> None:
        """Remove a secret (UC-06).

        Pre  caller.is_admin; the secret exists and is ACTIVE (UC-06 A2).
        Post status = REMOVED; permissions empty; index.remove_secret(secret_id) ran;
             the secret is absent from the next snapshot (FR-19).
        On failure the active set is unchanged (UC-06 A3).
        """
        raise NotImplementedError

    def pending_cases(self, caller: Token) -> list[VerificationCase]:
        """Return the verification queue (UC-07).

        Pre  caller.is_admin.
        Post every case is PENDING; an empty list is valid (UC-07 A1).
        """
        raise NotImplementedError

    def verify_case(self, caller: Token, case_id: UUID, label: Label) -> None:
        """Label a pending case and learn from it (UC-07, FR-17).

        Pre  Admin: caller.is_admin.
        Pre  Pending: the case exists and is PENDING.
        Post Verified: the case is VERIFIED.
        Post Learned: one new example with source = VERIFIED is stored,
             and indexed if its label is EXPOSURE.
        Post NewSnapshot: the secret is re-calibrated and a new snapshot is published.
        If saving fails, the case stays PENDING and no success is reported (UC-07 A2).
        """
        raise NotImplementedError

    def _index_secret(self, secret_id: UUID) -> None:
        """Index the secret's reference texts.

        Pre  the secret exists.
        Post the index holds one vector for the description (DESCRIPTION), one per
             prohibited detail (POLICY_DETAIL) and one per EXPOSURE example (EXAMPLE).
        """
        raise NotImplementedError

    def _calibrate_thresholds(self, secret_id: UUID) -> None:
        """Pick pass / block / ce thresholds from the secret's examples.

        Pre  examples of both labels exist.
        Post the Secret.Thresholds invariant holds.
        Hint: reach the recall target first (NFR-11), then the lowest false-positive
        rate (NFR-13).
        """
        raise NotImplementedError

    def _generate_examples(self, secret_id: UUID) -> None:
        """Background task: generate extra examples with the local LLM (FR-16).

        Not in diagram v11 (added on 2026-11-22; the ADD describes it under create).
        Post new examples have source = GENERATED; the exposure ones are indexed;
             the secret is re-calibrated.
        """
        raise NotImplementedError
