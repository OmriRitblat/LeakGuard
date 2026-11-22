"""«Alpha» HttpInspectionClient (ADD 5.2.11)."""

from __future__ import annotations

from leakguard.domain.common.value_objects import InspectionRequest, InspectionResult
from leakguard.infrastructure.litellm.inspection_client import InspectionClient


class HttpInspectionClient(InspectionClient):
    """Alpha: sends the request as JSON over HTTP to the LeakGuard service (PC-06),
    authenticated with service_token."""

    def __init__(self, url: str, service_token: str) -> None:
        self._url = url
        self._service_token = service_token

    async def inspect(self, request: InspectionRequest) -> InspectionResult:
        """POST the request and parse the result.

        An unreachable service, an HTTP error or a bad body raises an error, and the
        hook's FailurePolicy handles it.
        """
        raise NotImplementedError
