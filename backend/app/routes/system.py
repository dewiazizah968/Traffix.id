"""System routes for Traffix backend metadata and runtime status."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.runtime_status import runtime_status
from app.services.camera_service import camera_service
from core.config import settings
from core.constants import HORIZONS
from core.responses import success_response
from ml.model_loader import ml_fallback_active, models_loaded
from sim.tick_engine import tick_engine
from core.schemas import (
    StandardSuccessResponse,
    SystemRuntimeStatusResponse,
    SystemTimeResponse,
    SystemVersionInfoResponse,
)

WIB_TIMEZONE = ZoneInfo("Asia/Jakarta")

v1_router = APIRouter(
    prefix="/system",
    tags=["System"],
    responses={404: {"description": "System endpoint not found"}},
)

router = APIRouter(
    prefix="/api/system",
    tags=["System"],
    responses={404: {"description": "System endpoint not found"}},
)


def format_wib_time(value: datetime) -> str:
    """Format a datetime as an Asia/Jakarta time string.

    Args:
        value: Timezone-aware datetime value.

    Returns:
        Formatted WIB time string.
    """
    return value.astimezone(WIB_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S WIB")


@v1_router.get(
    "/ping",
    response_model=StandardSuccessResponse,
    summary="Ping",
    description="Returns a simple connectivity check response.",
)
async def ping(request: Request) -> JSONResponse:
    """Return a simple connectivity check response.

    Args:
        request: Incoming FastAPI request with request state.

    Returns:
        Standardized ping response with request tracing metadata.
    """
    return success_response(
        message="pong",
        data={"alive": True},
        request_id=request.state.request_id,
    )


@v1_router.get(
    "/version",
    response_model=StandardSuccessResponse,
    summary="Version",
    description="Returns backend service and API version metadata.",
)
async def v1_version(request: Request) -> JSONResponse:
    """Return backend version metadata.

    Args:
        request: Incoming FastAPI request with request state.

    Returns:
        Standardized response with service, app version, API version, and env.
    """
    return success_response(
        message="Backend metadata retrieved",
        data={
            "service": settings.app_name,
            "version": settings.app_version,
            "api_version": "v1",
            "environment": settings.app_env,
        },
        request_id=request.state.request_id,
    )


@v1_router.get(
    "/status",
    response_model=StandardSuccessResponse,
    summary="System Status",
    description="Returns placeholder runtime capability flags.",
)
async def v1_status(request: Request) -> JSONResponse:
    """Return system runtime capability status.

    Args:
        request: Incoming FastAPI request with request state.

    Returns:
        Standardized response with placeholder readiness flags.
    """
    snapshot = runtime_status.snapshot()
    camera_status = camera_service.status()
    return success_response(
        message="System status retrieved",
        data={
            "service": settings.app_name,
            "status": "operational",
            "ml_ready": models_loaded() or ml_fallback_active(),
            "ml_models_loaded": models_loaded(),
            "ml_fallback_active": ml_fallback_active(),
            "ml_mode": snapshot["ml_mode"],
            "weather_ready": True,
            "simulation_ready": snapshot["simulation_ready"],
            "simulation_active": tick_engine.is_running(),
            "dataset_ready": snapshot["dataset_ready"],
            "camera_ready": camera_status["frontend_ready"],
            "camera_status": {
                "configured_cameras": camera_status["configured_cameras"],
                "api_ready_cameras": camera_status["api_ready_cameras"],
                "metadata_loaded": camera_status["metadata_loaded"],
                "prediction_output_loaded": camera_status["prediction_output_loaded"],
                "yolo_output_loaded": camera_status["yolo_output_loaded"],
                "videos_available": camera_status["videos_available"],
                "videos_missing": camera_status["videos_missing"],
                "warnings": camera_status["warnings"],
            },
            "supported_horizons": HORIZONS,
        },
        request_id=request.state.request_id,
    )


@router.get(
    "/status",
    response_model=SystemRuntimeStatusResponse,
    summary="System Runtime Status",
    description="Returns backend runtime status without business logic.",
)
async def system_status() -> SystemRuntimeStatusResponse:
    """Return modular system runtime status.

    Returns:
        Typed system runtime status response.
    """
    snapshot = runtime_status.snapshot()
    return SystemRuntimeStatusResponse(
        service=settings.app_name,
        status="operational",
        ml_models_loaded=models_loaded() or ml_fallback_active(),
        simulation_active=tick_engine.is_running(),
        weather_service="local-simulation",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/time",
    response_model=SystemTimeResponse,
    summary="System Time",
    description="Returns current backend time in Asia/Jakarta timezone.",
)
async def system_time() -> SystemTimeResponse:
    """Return current system time in WIB.

    Returns:
        Typed system time response.
    """
    current_time = datetime.now(WIB_TIMEZONE)
    return SystemTimeResponse(
        timezone="Asia/Jakarta",
        current_time_wib=format_wib_time(current_time),
        unix=int(current_time.timestamp()),
    )


@router.get(
    "/version",
    response_model=SystemVersionInfoResponse,
    summary="System Version",
    description="Returns backend application version metadata.",
)
async def system_version() -> SystemVersionInfoResponse:
    """Return modular system version metadata.

    Returns:
        Typed system version response.
    """
    return SystemVersionInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )
