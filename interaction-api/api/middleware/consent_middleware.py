"""
Standalone consent-gate dependency.

NOTE: event ingestion (`/interactions/events`) already runs its consent
check inside `validation/event_validator.py` as part of the versioned
contract pipeline — you don't need to add this dependency there too.
This is for any *other* endpoint (future ones, e.g. a "recommend now"
trigger) that wants to gate on consent before doing anything else.
"""
from fastapi import Depends, HTTPException, status

from ...models.event_types import EventCategory
from ...validation.consent_checker import ConsentChecker
from .auth_middleware import authenticate_request

_consent_checker = ConsentChecker()


def require_consent(category: EventCategory):
    """Returns a FastAPI dependency that 403s if `user_id` lacks the scopes
    required for `category`. Usage:

        @router.post("/some-route")
        async def handler(user_id: str = Depends(require_consent(EventCategory.CHAT))):
            ...
    """

    async def _dependency(user_id: str = Depends(authenticate_request)) -> str:
        result = await _consent_checker.check(user_id, category)
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "consent_required", "missing_scopes": result.missing_scopes},
            )
        return user_id

    return _dependency
