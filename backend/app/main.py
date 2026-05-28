"""FastAPI application factory and system endpoints for Traffix."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import time
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import api_router
from app.bootstrap import shutdown_integrations, startup_integrations
from app.middleware import request_tracking_middleware
from app.routes.system import router as system_router
from core.config import settings
from core.constants import HORIZONS
from core.exceptions import TraffixAPIException
from core.logger import get_logger
from core.request_context import generate_request_id
from core.responses import error_response, success_response
from core.schemas import StandardSuccessResponse

system_logger = get_logger("system")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle.

    Args:
        app: FastAPI application instance.

    Yields:
        Control back to FastAPI while the application is running.
    """
    system_logger.info("Starting Traffix backend")
    system_logger.info("Service version: %s", settings.app_version)
    system_logger.info("Environment: %s", settings.app_env)
    system_logger.info("Supported horizons: %s", HORIZONS)
    system_logger.info("Camera input enabled: %s", settings.camera_input_enabled)
    await startup_integrations()
    yield
    await shutdown_integrations()
    system_logger.info("Shutting down Traffix backend")


def _request_id_from_request(request: Request) -> str:
    """Return request ID from state, creating a fallback when absent.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Request tracing identifier.
    """
    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = generate_request_id()
        request.state.request_id = request_id
    return request_id


def _validation_error_details(
    exc: RequestValidationError,
) -> list[dict[str, Any]]:
    """Format FastAPI validation errors for frontend parsing.

    Args:
        exc: FastAPI request validation exception.

    Returns:
        List of simplified validation error dictionaries.
    """
    return [
        {
            "loc": list(error.get("loc", [])),
            "msg": error.get("msg", ""),
            "type": error.get("type", ""),
        }
        for error in exc.errors()
    ]


def _with_trace_headers(
    response: JSONResponse,
    request: Request,
) -> JSONResponse:
    """Attach tracing headers to an exception response.

    Args:
        response: JSON response created by an exception handler.
        request: Incoming FastAPI request.

    Returns:
        JSON response with request tracing headers.
    """
    request_id = _request_id_from_request(request)
    start_time = getattr(request.state, "process_start_time", None)
    process_time = 0.0
    if start_time is not None:
        process_time = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"
    return response


def create_app() -> FastAPI:
    """Create and configure the Traffix FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Traffix backend for AI-powered smart traffic management. "
            "Integrates LSTM multi-horizon predictions "
            f"({', '.join(HORIZONS)}), YOLO vehicle detection, BMKG weather, "
            "and real-time traffic simulation."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(request_tracking_middleware)
    app.include_router(api_router)
    app.include_router(system_router)

    @app.exception_handler(TraffixAPIException)
    async def traffix_api_exception_handler(
        request: Request,
        exc: TraffixAPIException,
    ) -> JSONResponse:
        """Handle expected Traffix API exceptions.

        Args:
            request: Incoming FastAPI request.
            exc: Raised Traffix API exception.

        Returns:
            Standardized error JSON response.
        """
        system_logger.warning(
            "TraffixAPIException %s: %s",
            exc.code,
            exc.message,
        )
        response = error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            status_code=exc.status_code,
            request_id=_request_id_from_request(request),
        )
        return _with_trace_headers(response, request)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle FastAPI request validation exceptions.

        Args:
            request: Incoming FastAPI request.
            exc: Raised request validation exception.

        Returns:
            Standardized validation error JSON response.
        """
        system_logger.warning(
            "Request validation failed: %s",
            _validation_error_details(exc),
        )
        response = error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details=_validation_error_details(exc),
            status_code=422,
            request_id=_request_id_from_request(request),
        )
        return _with_trace_headers(response, request)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Handle FastAPI and Starlette HTTP exceptions.

        Args:
            request: Incoming FastAPI request.
            exc: Raised HTTP exception.

        Returns:
            Standardized HTTP error JSON response.
        """
        system_logger.warning("HTTP error %s: %s", exc.status_code, exc.detail)
        response = error_response(
            code="HTTP_ERROR",
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=_request_id_from_request(request),
        )
        return _with_trace_headers(response, request)

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected server exceptions safely.

        Args:
            request: Incoming FastAPI request.
            exc: Raised unexpected exception.

        Returns:
            Standardized internal server error JSON response.
        """
        system_logger.exception("Unhandled server exception: %s", exc)
        response = error_response(
            code="INTERNAL_SERVER_ERROR",
            message="Unexpected server error",
            status_code=500,
            request_id=_request_id_from_request(request),
        )
        return _with_trace_headers(response, request)

    @app.get(
        "/",
        response_model=StandardSuccessResponse,
        tags=["System"],
        summary="Welcome",
    )
    async def root(request: Request) -> JSONResponse:
        """Return API welcome metadata.

        Args:
            request: Incoming FastAPI request with request state.

        Returns:
            Standardized response with links to documentation and health.
        """
        return success_response(
            message="Traffix Backend API - AI-Powered Smart Traffic Management",
            data={
                "message": (
                    "Traffix Backend API - AI-Powered Smart Traffic Management"
                ),
                "version": settings.app_version,
                "docs": "/docs",
                "health": "/health",
                "ml_horizons": HORIZONS,
            },
            request_id=request.state.request_id,
        )

    @app.get(
        "/health",
        response_model=StandardSuccessResponse,
        tags=["System"],
        summary="Health Check",
        description=(
            "Returns liveness status and supported ML prediction horizons."
        ),
    )
    async def health(request: Request) -> JSONResponse:
        """Return service liveness and supported ML horizons.

        Args:
            request: Incoming FastAPI request with request state.

        Returns:
            Standardized health response payload.
        """
        return success_response(
            message="Service is healthy",
            data={
                "service": settings.app_name,
                "version": settings.app_version,
                "status": "ok",
                "environment": settings.app_env,
                "ml_horizons_supported": HORIZONS,
            },
            request_id=request.state.request_id,
        )

    return app


app = create_app()
