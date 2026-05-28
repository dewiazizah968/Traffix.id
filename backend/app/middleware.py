"""HTTP middleware utilities for Traffix backend."""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from core.logger import get_logger
from core.request_context import generate_request_id

api_logger = get_logger("api")


async def request_tracking_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach request tracing metadata to every HTTP response.

    Args:
        request: Incoming FastAPI request.
        call_next: Next middleware or route handler in the stack.

    Returns:
        Response with request ID and process time headers.
    """
    request_id = generate_request_id()
    request.state.request_id = request_id
    start_time = time.perf_counter()
    request.state.process_start_time = start_time

    api_logger.info("%s %s started", request.method, request.url.path)

    try:
        response = await call_next(request)
    except Exception:
        process_time = time.perf_counter() - start_time
        api_logger.exception(
            "%s %s -> 500 (%.1fms)",
            request.method,
            request.url.path,
            process_time * 1000,
        )
        raise
    else:
        process_time = time.perf_counter() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        api_logger.info(
            "%s %s -> %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            process_time * 1000,
        )
        return response
