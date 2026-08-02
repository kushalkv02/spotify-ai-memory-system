"""Custom exception hierarchy for the interaction pipeline."""


class InteractionAPIError(Exception):
    """Base class for all interaction-api errors."""


class AuthenticationError(InteractionAPIError):
    """Raised when a request cannot be authenticated."""


class ConsentDeniedError(InteractionAPIError):
    """Raised when the user has not granted consent for the requested capture."""

    def __init__(self, missing_scopes: list[str]):
        self.missing_scopes = missing_scopes
        super().__init__(f"Missing consent scopes: {missing_scopes}")


class EventValidationError(InteractionAPIError):
    """Raised when an incoming event fails schema / semantic validation."""


class UnsupportedEventVersionError(EventValidationError):
    """Raised when an event's schema_version isn't supported."""


class PersistenceError(InteractionAPIError):
    """Raised when the raw event fails to persist to Postgres."""


class DuplicateEventError(PersistenceError):
    """Raised when an event_id has already been ingested (idempotency)."""


class GraphWritebackError(InteractionAPIError):
    """Raised when writing through to the `graph` package fails.

    Intentionally non-fatal for the API response — an event that's safely in
    Postgres should not be lost just because Neo4j writeback failed; callers
    should log and continue rather than raise this all the way to the client.
    """
