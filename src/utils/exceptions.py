"""Project-specific exceptions so callers can handle failures precisely."""


class QAssistError(Exception):
    """Base class for all project errors."""


class LLMUnavailableError(QAssistError):
    """LLM cannot be used (no key, bad key, network, timeout, rate limit...)."""

    def __init__(self, message: str, kind: str = "other"):
        super().__init__(message)
        self.kind = kind  # no_key | invalid_credentials | rate_limit | timeout | network | malformed | other


class KnowledgeBaseError(QAssistError):
    """Problem loading or indexing knowledge-base documents."""


class DatabaseError(QAssistError):
    """Wrapped database failure with a readable message."""
