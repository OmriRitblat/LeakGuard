"""InspectionService (ADD 5.2.1)."""

from __future__ import annotations

from leakguard.domain.common.value_objects import InspectionRequest, InspectionResult
from leakguard.domain.inspection.pipeline import InspectionPipeline
from leakguard.domain.inspection_record.repository import InspectionRecordRepository
from leakguard.domain.secret.repository import SecretRepository
from leakguard.domain.user.repository import UserRepository
from leakguard.domain.verification.repository import VerificationCaseRepository


class InspectionService:
    """Runs UC-02 inside LeakGuard.

    1. Checks that the user exists (UC-02 step 3).
    2. Takes the current SecretSnapshot once and builds an InspectionContext with a
       deadline of now + time_limit_ms.
    3. Runs the pipeline.
    4. Saves one InspectionRecord and opens a VerificationCase for each candidate
       still UNCERTAIN (FR-20, FR-28).

    Retries and fail-open / fail-closed are NOT here: they sit in the hook's
    FailurePolicy, the only place that also sees a service that is down.
    Set time_limit_ms below FailurePolicy.timeout_ms, so the service answers
    before the hook gives up.
    """

    def __init__(
        self,
        pipeline: InspectionPipeline,
        users: UserRepository,
        secrets: SecretRepository,
        records: InspectionRecordRepository,
        cases: VerificationCaseRepository,
        time_limit_ms: int,
    ) -> None:
        self._pipeline = pipeline
        self._users = users
        self._secrets = secrets
        self._records = records
        self._cases = cases
        self._time_limit_ms = time_limit_ms

    async def inspect(self, request: InspectionRequest) -> InspectionResult:
        """Inspect one request.

        Pre  HasText:   request.texts is not empty.
        Pre  KnownUser: users.find_by_email(request.user_ref) is not None (UC-02 step 3);
                        otherwise raises UnknownUserError.
        Post OneRecord: exactly one new InspectionRecord.
        Post SameSnapshot: record.snapshot_version = context.snapshot.version (INV-05).
        Post ExposureBlocks: a SECRET_EXPOSURE finding implies decision = BLOCK.
        Post DecidedWhenComplete: result.completed implies a decision.
        When the deadline passes, returns completed = False and the hook's FailurePolicy decides.
        Never writes the prompt into the record (NFR-05).

        Hint: the pipeline is CPU-bound and synchronous; run it in a worker thread
        so the LiteLLM event loop is not blocked.
        """
        raise NotImplementedError
