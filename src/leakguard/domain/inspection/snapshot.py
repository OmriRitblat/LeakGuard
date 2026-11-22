"""SecretSnapshot and SecretRule (ADD 5.2.4)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SecretRule:
    """«value object» The decrypted detection data of one ACTIVE secret.

    Invariant Thresholds: 0 <= pass_threshold < block_threshold <= 1.
    """

    secret_id: UUID
    code: str
    description: str
    policy_text: str
    pass_threshold: float
    block_threshold: float
    ce_threshold: float


@dataclass(frozen=True)
class SecretSnapshot:
    """«value object» An immutable, versioned copy of the ACTIVE secrets.

    One request uses one snapshot from start to end (INV-05). A change to any
    secret builds a new snapshot; an existing one never changes. Publishing a new
    snapshot is one atomic reference assignment, so readers need no lock.

    Invariants:
      - UniqueRule: rules are unique by secret_id;
      - Thresholds: every rule satisfies 0 <= pass_threshold < block_threshold <= 1.
    """

    version: int
    rules: tuple[SecretRule, ...]

    def get(self, secret_id: UUID) -> SecretRule:
        """Return the rule of this secret.

        Pre Known: a rule with this secret_id exists.
        """
        raise NotImplementedError
