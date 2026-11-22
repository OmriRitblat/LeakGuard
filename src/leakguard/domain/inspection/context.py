"""InspectionContext and Candidate: the per-request working state (ADD 5.2.3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from leakguard.domain.common.enums import Decision
from leakguard.domain.common.value_objects import Finding
from leakguard.domain.inspection.match import Match
from leakguard.domain.inspection.snapshot import SecretSnapshot


class CandidateStatus(Enum):
    """Candidate.status."""

    EXPOSED = "EXPOSED"
    SAFE = "SAFE"
    UNCERTAIN = "UNCERTAIN"


@dataclass
class Candidate:
    """One secret the embedding stage judged close enough to check further.

    Keeps its best Matches (for example the top 5), so the Cross-Encoder's cost stays bounded.

    Invariants:
      - HasMatches: matches is not empty;
      - MatchesOfThisSecret: every match has this secret_id;
      - BestMatch: similarity = max(m.similarity for m in matches).
    """

    secret_id: UUID
    similarity: float
    status: CandidateStatus
    ce_score: float | None = None
    matches: list[Match] = field(default_factory=list)


@dataclass
class InspectionContext:
    """The per-request working object every stage reads and adds to.

    Stages are stateless and shared between concurrent requests, so all
    per-request state lives here.

    Invariants:
      - OneCandidatePerSecret: candidates are unique by secret_id;
      - CandidateInSnapshot: every candidate's secret is in snapshot.rules (INV-05);
      - NoChangeWithoutFinding: current_text <> original_text implies a PII finding.

    ``deadline`` is a monotonic-clock time (now + time_limit_ms); check it before
    every model call.
    """

    original_text: str
    current_text: str
    snapshot: SecretSnapshot
    deadline: float
    findings: list[Finding] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    decision: Decision | None = None
