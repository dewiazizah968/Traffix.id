"""Weather routes for traffic context."""

from fastapi import APIRouter, HTTPException, Query, Request

from core.responses import success_response
from core.schemas import StandardSuccessResponse
from weather.service import weather_service

router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.get(
    "/current",
    response_model=StandardSuccessResponse,
    summary="Current Weather Context",
    description="Returns local weather context for the city or one intersection.",
)
async def current_weather(
    request: Request,
    intersection_id: str | None = Query(default=None),
) -> StandardSuccessResponse:
    """Return current traffic-weather context.

    Args:
        request: Incoming FastAPI request.
        intersection_id: Optional target intersection identifier.

    Returns:
        Standardized weather response.

    Raises:
        HTTPException: When the intersection is unknown.
    """
    try:
        payload = weather_service.current(
            intersection_id.upper() if intersection_id else None,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return success_response(
        message="Weather context retrieved",
        data=payload,
        request_id=request.state.request_id,
    )


@router.get(
    "/forecast",
    response_model=StandardSuccessResponse,
    summary="Weather Forecast",
    description="Returns a lightweight hourly forecast for traffic planning.",
)
async def weather_forecast(
    request: Request,
    hours: int = Query(default=6, ge=1, le=24),
) -> StandardSuccessResponse:
    """Return local weather forecast.

    Args:
        request: Incoming FastAPI request.
        hours: Forecast horizon in hours.

    Returns:
        Standardized forecast response.
    """
    forecast = weather_service.forecast(hours=hours)
    return success_response(
        message="Weather forecast retrieved",
        data={"hours": hours, "forecast": forecast},
        request_id=request.state.request_id,
    )
