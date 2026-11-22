"""Enumerations shared across the domain."""

from __future__ import annotations

from enum import Enum


class Label(Enum):
    """«enumeration» Label: the label of an example or a verification case."""

    EXPOSURE = "EXPOSURE"
    NON_EXPOSURE = "NON_EXPOSURE"


class Decision(Enum):
    """«enumeration» Decision: the outcome of one inspection (FR-06)."""

    ALLOW = "ALLOW"
    REDACT = "REDACT"
    BLOCK = "BLOCK"


class FindingType(Enum):
    """Finding.type: PII | SECRET_EXPOSURE."""

    PII = "PII"
    SECRET_EXPOSURE = "SECRET_EXPOSURE"
