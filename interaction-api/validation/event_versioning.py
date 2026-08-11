"""
Handles versioning of the Event Contract.

Only one version exists today (1.0.0), but this keeps a seam for future
client migrations without touching the validator or routes.
"""
from ..config import settings
import uuid

from ..models.event import EventEnvelope
from ..models.event_types import ConsentState, EventSurface
from ..utils.exceptions import UnsupportedEventVersionError


class EventSchemaRegistry:
    def __init__(self):
        self.supported_versions = set(settings.supported_event_schema_versions)
        self.current_version = settings.current_event_schema_version

    def is_supported(self, version: str) -> bool:
        return version in self.supported_versions

    def migrate_to_current(self, envelope: EventEnvelope) -> EventEnvelope:
        """Upgrade an older-versioned envelope's payload to the current schema.

        v1.0 events are upgraded by adding server-safe values for the v1.1
        provenance contract.  A deterministic key preserves retry safety.
        """
        if not self.is_supported(envelope.schema_version):
            raise UnsupportedEventVersionError(
                f"schema_version '{envelope.schema_version}' is not supported "
                f"(supported: {sorted(self.supported_versions)})"
            )
        if envelope.schema_version == "1.0.0":
            return envelope.model_copy(update={
                "schema_version": self.current_version,
                "subject_scope": envelope.subject_scope or "user",
                "surface": EventSurface.UNKNOWN,
                "locale": envelope.locale or "und",
                "consent_state": ConsentState.PENDING,
                "idempotency_key": str(uuid.uuid5(uuid.NAMESPACE_URL, f"legacy-event:{envelope.event_id}")),
            })
        return envelope
