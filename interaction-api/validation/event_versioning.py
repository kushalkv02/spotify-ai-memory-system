"""
Handles versioning of the Event Contract.

Only one version exists today (1.0.0), but this keeps a seam for future
client migrations without touching the validator or routes.
"""
from ..config import settings
from ..models.event import EventEnvelope
from ..utils.exceptions import UnsupportedEventVersionError


class EventSchemaRegistry:
    def __init__(self):
        self.supported_versions = set(settings.supported_event_schema_versions)
        self.current_version = settings.current_event_schema_version

    def is_supported(self, version: str) -> bool:
        return version in self.supported_versions

    def migrate_to_current(self, envelope: EventEnvelope) -> EventEnvelope:
        """Upgrade an older-versioned envelope's payload to the current schema.

        No-op today since only one version is supported. When a v1.1.0 lands,
        add an `if envelope.schema_version == "1.0.0": ...transform...` branch
        here rather than in the validator.
        """
        if not self.is_supported(envelope.schema_version):
            raise UnsupportedEventVersionError(
                f"schema_version '{envelope.schema_version}' is not supported "
                f"(supported: {sorted(self.supported_versions)})"
            )
        return envelope
