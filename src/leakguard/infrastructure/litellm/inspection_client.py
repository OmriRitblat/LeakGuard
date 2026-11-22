"""«interface» InspectionClient (ADD 5.2.11)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from leakguard.domain.common.value_objects import InspectionRequest, InspectionResult


class InspectionClient(ABC):
    """How the hook reaches LeakGuard: in the same process (POC) or over HTTP (Alpha)."""

    @abstractmethod
    async def inspect(self, request: InspectionRequest) -> InspectionResult:
        """Send one request to LeakGuard and return its result.

        Any failure (exception, unreachable service, malformed answer) is raised,
        and the hook's FailurePolicy handles it.
        """
