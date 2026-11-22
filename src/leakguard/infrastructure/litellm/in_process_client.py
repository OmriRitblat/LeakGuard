"""«POC» InProcessInspectionClient (ADD 5.2.11)."""

from __future__ import annotations

from leakguard.application.inspection_service import InspectionService
from leakguard.domain.common.value_objects import InspectionRequest, InspectionResult
from leakguard.infrastructure.litellm.inspection_client import InspectionClient


class InProcessInspectionClient(InspectionClient):
    """POC: calls InspectionService directly inside the LiteLLM process.

    No network; the models load inside LiteLLM.
    """

    def __init__(self, service: InspectionService) -> None:
        self._service = service

    async def inspect(self, request: InspectionRequest) -> InspectionResult:
        """Delegate to InspectionService.inspect."""
        raise NotImplementedError
