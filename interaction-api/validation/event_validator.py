"""
Event Validation Layer.

     ▼ (Validate + Authenticate + Consent Check)
Event Validation Layer
     │
     ▼ (Valid Versioned Event Contract)
PostgreSQL

Authentication happens earlier (api/middleware/auth_middleware.py resolves
user_id before this layer ever runs). This layer covers: version support,
payload shape, and consent.
"""
from ..models.event import EventEnvelope, ValidatedEvent
from ..models.event_types import ConsentState, EventCategory, PlaybackAction, UIActionType
from ..utils.exceptions import ConsentDeniedError, EventValidationError
from ..utils.timestamps import utc_now
from .event_versioning import EventSchemaRegistry
from .consent_checker import ConsentChecker


class EventValidator:
    def __init__(self, schema_registry: EventSchemaRegistry, consent_checker: ConsentChecker):
        self.schema_registry = schema_registry
        self.consent_checker = consent_checker

    async def validate(self, envelope: EventEnvelope) -> ValidatedEvent:
        # 1. version check + migration
        envelope = self.schema_registry.migrate_to_current(envelope)

        # 2. category-specific payload shape check
        self.validate_payload_for_category(envelope)

        # 3. consent check
        result = await self.consent_checker.check(envelope.user_id, envelope.category)
        if not result.allowed:
            raise ConsentDeniedError(result.missing_scopes)

        # 4. stamp + freeze
        # A client may not claim consent. The server records the result.
        return ValidatedEvent(
            **envelope.model_dump(exclude={"consent_state"}),
            consent_state=ConsentState.GRANTED,
            received_at=utc_now(),
            consent_scopes_checked=self.consent_checker.required_scopes_for(envelope.category),
        )

    def validate_payload_for_category(self, envelope: EventEnvelope) -> None:
        payload = envelope.payload

        if envelope.category == EventCategory.PLAYBACK:
            if "track_id" not in payload:
                raise EventValidationError("playback events require payload.track_id")
            if "action" not in payload:
                raise EventValidationError("playback events require payload.action")
            try:
                PlaybackAction(payload["action"])
            except ValueError:
                raise EventValidationError(f"unknown playback action: {payload['action']}")

        elif envelope.category == EventCategory.CHAT:
            if not payload.get("message"):
                raise EventValidationError("chat events require a non-empty payload.message")

        elif envelope.category == EventCategory.UI_ACTION:
            if "action_type" not in payload:
                raise EventValidationError("ui_action events require payload.action_type")
            try:
                action_type = UIActionType(payload["action_type"])
            except ValueError:
                raise EventValidationError(f"unknown ui action_type: {payload['action_type']}")
            if action_type in {UIActionType.FOLLOW_ARTIST, UIActionType.UNFOLLOW_ARTIST} and "artist_id" not in payload:
                raise EventValidationError(f"{action_type.value} events require payload.artist_id")
