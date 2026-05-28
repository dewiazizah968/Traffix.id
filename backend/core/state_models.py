"""Typed runtime state models for Traffix backend."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format.

    Returns:
        Current UTC timestamp string.
    """
    return datetime.now(timezone.utc).isoformat()


class TrafficMetrics(BaseModel):
    """Current traffic metrics for an intersection."""

    vehicle_count: int = Field(default=0, ge=0)
    avg_speed_kmh: float = Field(default=0.0, ge=0.0)
    congestion_level: str = Field(default="low")
    density_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    queue_length_veh: int = Field(default=0, ge=0)
    updated_at: str = Field(default_factory=utc_now_iso)


class WeatherState(BaseModel):
    """Current weather state shared by runtime services."""

    condition: str = Field(default="unknown")
    temperature_c: float | None = Field(default=None)
    humidity_percent: float | None = Field(default=None)
    rainfall_mm: float | None = Field(default=None)
    source: str = Field(default="manual")
    updated_at: str = Field(default_factory=utc_now_iso)


class RecommendationState(BaseModel):
    """Current signal recommendation for an intersection."""

    active: bool = Field(default=False)
    recommendation: str | None = Field(default=None)
    reason: str | None = Field(default=None)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    updated_at: str = Field(default_factory=utc_now_iso)


class CameraState(BaseModel):
    """Current camera status for an intersection."""

    camera_id: str | None = Field(default=None)
    enabled: bool = Field(default=False)
    online: bool = Field(default=False)
    last_frame_at: str | None = Field(default=None)
    vehicle_count: int = Field(default=0, ge=0)
    updated_at: str = Field(default_factory=utc_now_iso)


class IntersectionState(BaseModel):
    """Runtime state for one managed traffic intersection."""

    intersection_id: int = Field(ge=1)
    name: str
    traffic: TrafficMetrics = Field(default_factory=TrafficMetrics)
    recommendation: RecommendationState = Field(
        default_factory=RecommendationState,
    )
    camera: CameraState = Field(default_factory=CameraState)
    ai_predictions: dict[str, float | None] = Field(default_factory=dict)
    signal_timing: dict[str, int] = Field(
        default_factory=lambda: {
            "red_seconds": 60,
            "yellow_seconds": 5,
            "green_seconds": 45,
        }
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=utc_now_iso)
