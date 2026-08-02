"""
Consent Check — part of the 'Validate + Authenticate + Consent Check' step.

NOTE: This is an in-memory placeholder store so the API is testable end to
end today. Swap `_GRANTED_SCOPES` for a real Postgres-backed consents table
(e.g. a `user_consents` table in the event-store service) once that's built.
"""
from ..config import settings
from ..models.consent import ConsentCheckResult
from ..models.event_types import EventCategory
from ..utils.logger import get_logger

logger = get_logger(__name__)

# user_id -> set of granted scopes. Populate via a real /consents endpoint later.
_GRANTED_SCOPES: dict[str, set[str]] = {}


class ConsentChecker:
    def required_scopes_for(self, category: EventCategory) -> list[str]:
        return settings.consent_required_scopes.get(category.value, [])

    async def check(self, user_id: str, category: EventCategory) -> ConsentCheckResult:
        required = set(self.required_scopes_for(category))

        if settings.debug and settings.allow_dev_consent_bypass:
            logger.debug("Dev consent bypass active for user_id=%s", user_id)
            return ConsentCheckResult(allowed=True, missing_scopes=[])

        granted = _GRANTED_SCOPES.get(user_id, set())
        missing = sorted(required - granted)
        return ConsentCheckResult(allowed=not missing, missing_scopes=missing)

    def grant(self, user_id: str, scopes: list[str]) -> None:
        """Helper for tests/dev — records consent grants in-memory."""
        _GRANTED_SCOPES.setdefault(user_id, set()).update(scopes)
