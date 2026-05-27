"""Custom exception architecture for Traffix backend."""

from typing import Any


class TraffixAPIException(Exception):
    """Base exception for expected Traffix API errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: list[Any] | None = None,
    ) -> None:
        """Initialize a Traffix API exception.

        Args:
            code: Stable machine-readable error code.
            message: Human-readable error message.
            status_code: HTTP response status code.
            details: Optional structured error details.
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details if details is not None else []
