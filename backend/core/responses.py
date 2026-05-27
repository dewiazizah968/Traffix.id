"""Standardized JSON response builders for Traffix backend."""

from datetime import datetime, timezone
from typing import Any

from fastapi.responses import JSONResponse


def _utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO format.

    Returns:
        Current UTC ISO timestamp.
    """
    return datetime.now(timezone.utc).isoformat()


def success_response(
    message: str,
    data: dict[str, Any] | list[Any] | None,
    request_id: str,
    status_code: int = 200,
) -> JSONResponse:
    """Build a standardized success JSON response.

    Args:
        message: Human-readable success message.
        data: Response payload data.
        request_id: Request tracing identifier.
        status_code: HTTP response status code.

    Returns:
        Standardized FastAPI JSON response.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data if data is not None else {},
            "request_id": request_id,
            "timestamp": _utc_timestamp(),
        },
    )


def error_response(
    code: str,
    message: str,
    request_id: str,
    details: list[Any] | None = None,
    status_code: int = 400,
) -> JSONResponse:
    """Build a standardized error JSON response.

    Args:
        code: Stable machine-readable error code.
        message: Human-readable error message.
        request_id: Request tracing identifier.
        details: Optional structured error details.
        status_code: HTTP response status code.

    Returns:
        Standardized FastAPI JSON response.
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details if details is not None else [],
            },
            "request_id": request_id,
            "timestamp": _utc_timestamp(),
        },
    )
