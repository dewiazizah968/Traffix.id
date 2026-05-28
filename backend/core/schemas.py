"""Pydantic v2 API contracts for Traffix backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

JsonPrimitive: TypeAlias = str | int | float | bool | None
JsonFlatObject: TypeAlias = dict[str, JsonPrimitive | list[JsonPrimitive]]
JsonPayload: TypeAlias = (
    JsonFlatObject | list[JsonFlatObject] | list[JsonPrimitive]
)


def _validate_utc_iso_timestamp(value: str) -> str:
    """Validate an ISO-8601 timestamp with UTC timezone.

    Args:
        value: Timestamp string to validate.

    Returns:
        The original timestamp string when valid.

    Raises:
        ValueError: If the timestamp is not ISO-8601 UTC.
    """
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be valid ISO-8601") from exc

    offset = parsed.utcoffset()
    if parsed.tzinfo is None or offset is None:
        raise ValueError("timestamp must include UTC timezone")
    if offset != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return value


class BaseResponse(BaseModel):
    """Base API response contract.

    Attributes:
        success: Whether the request completed successfully.
        message: Human-readable response message.
        timestamp: ISO-8601 UTC response timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Request successful",
                "timestamp": "2026-05-27T22:37:00+00:00",
            }
        },
    )

    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Human-readable response message")
    timestamp: str = Field(description="ISO-8601 UTC response timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate response timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class TrafficMetrics(BaseModel):
    """Traffic measurement contract for an intersection.

    Attributes:
        vehicle_count: Number of vehicles in the observed interval.
        avg_speed: Average vehicle speed in kilometers per hour.
        occupancy_rate: Lane occupancy ratio from 0 to 1.
        queue_length: Number of queued vehicles.
        wait_time_seconds: Estimated wait time in seconds.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "vehicle_count": 42,
                "avg_speed": 28.5,
                "occupancy_rate": 0.67,
                "queue_length": 12,
                "wait_time_seconds": 90,
            }
        },
    )

    vehicle_count: int = Field(
        ge=0,
        strict=True,
        description="Number of vehicles in the observed interval",
    )
    avg_speed: float = Field(
        ge=0.0,
        strict=True,
        description="Average vehicle speed in kilometers per hour",
    )
    occupancy_rate: float = Field(
        ge=0.0,
        le=1.0,
        strict=True,
        description="Lane occupancy ratio from 0 to 1",
    )
    queue_length: int = Field(
        ge=0,
        strict=True,
        description="Number of queued vehicles",
    )
    wait_time_seconds: int = Field(
        ge=0,
        strict=True,
        description="Estimated wait time in seconds",
    )


class WeatherState(BaseModel):
    """Weather state contract for traffic context.

    Attributes:
        condition: Normalized weather condition.
        temperature_celsius: Ambient temperature in Celsius.
        humidity_percent: Relative humidity percentage.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "condition": "Rain",
                "temperature_celsius": 27.5,
                "humidity_percent": 82.0,
            }
        },
    )

    condition: Literal["Sunny", "Cloudy", "Rain", "Storm"] = Field(
        description="Normalized weather condition",
    )
    temperature_celsius: float = Field(
        strict=True,
        description="Ambient temperature in Celsius",
    )
    humidity_percent: float = Field(
        ge=0.0,
        le=100.0,
        strict=True,
        description="Relative humidity percentage from 0 to 100",
    )


class IntersectionState(BaseModel):
    """Live-state contract for one traffic intersection.

    Attributes:
        intersection_id: Stable intersection identifier.
        intersection_name: Human-readable intersection name.
        timestamp: ISO-8601 UTC observation timestamp.
        traffic: Current traffic metrics.
        weather: Current weather state.
        signal_state: Current traffic signal state.
        green_duration_seconds: Current green-light duration.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "intersection_id": "int-001",
                "intersection_name": "Intersection 1",
                "timestamp": "2026-05-27T22:37:00+00:00",
                "traffic": {
                    "vehicle_count": 42,
                    "avg_speed": 28.5,
                    "occupancy_rate": 0.67,
                    "queue_length": 12,
                    "wait_time_seconds": 90,
                },
                "weather": {
                    "condition": "Rain",
                    "temperature_celsius": 27.5,
                    "humidity_percent": 82.0,
                },
                "signal_state": "GREEN",
                "green_duration_seconds": 45,
            }
        },
    )

    intersection_id: str = Field(description="Stable intersection identifier")
    intersection_name: str = Field(description="Human-readable name")
    timestamp: str = Field(description="ISO-8601 UTC observation timestamp")
    traffic: TrafficMetrics = Field(description="Current traffic metrics")
    weather: WeatherState = Field(description="Current weather state")
    signal_state: Literal["RED", "YELLOW", "GREEN"] = Field(
        description="Current traffic signal state",
    )
    green_duration_seconds: int = Field(
        ge=5,
        strict=True,
        description="Current green-light duration in seconds",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate observation timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class PredictionRequest(BaseModel):
    """Prediction request contract.

    Attributes:
        intersection_id: Target intersection identifier.
        horizon: Prediction horizon requested by the client.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "intersection_id": "int-001",
                "horizon": "15m",
            }
        },
    )

    intersection_id: str = Field(description="Target intersection identifier")
    horizon: Literal["15m", "2h", "4h"] = Field(
        description="Prediction horizon",
    )


class PredictionResponse(BaseResponse):
    """Prediction response contract.

    Attributes:
        intersection_id: Target intersection identifier.
        horizon: Prediction horizon used by the model.
        predicted_vehicle_count: Predicted vehicle count.
        predicted_congestion_level: Predicted congestion class.
        confidence_score: Model confidence score from 0 to 1.
        prediction_timestamp: ISO-8601 UTC prediction timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Prediction generated",
                "timestamp": "2026-05-27T22:37:00+00:00",
                "intersection_id": "int-001",
                "horizon": "15m",
                "predicted_vehicle_count": 58,
                "predicted_congestion_level": "High",
                "confidence_score": 0.91,
                "prediction_timestamp": "2026-05-27T22:37:00+00:00",
            }
        },
    )

    intersection_id: str = Field(description="Target intersection identifier")
    horizon: Literal["15m", "2h", "4h"] = Field(
        description="Prediction horizon used by the model",
    )
    predicted_vehicle_count: int = Field(
        ge=0,
        strict=True,
        description="Predicted vehicle count",
    )
    predicted_congestion_level: Literal[
        "Low",
        "Medium",
        "High",
        "Critical",
    ] = Field(description="Predicted congestion class")
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        strict=True,
        description="Model confidence score from 0 to 1",
    )
    prediction_timestamp: str = Field(
        description="ISO-8601 UTC prediction timestamp",
    )

    @field_validator("prediction_timestamp")
    @classmethod
    def validate_prediction_timestamp(cls, value: str) -> str:
        """Validate prediction timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class RecommendationResponse(BaseResponse):
    """Signal recommendation response contract.

    Attributes:
        intersection_id: Target intersection identifier.
        current_green_seconds: Current green-light duration.
        recommended_green_seconds: Recommended green-light duration.
        delta_seconds: Difference from current to recommended duration.
        reason: Human-readable recommendation reason.
        congestion_risk_percent: Congestion risk percentage.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Recommendation generated",
                "timestamp": "2026-05-27T22:37:00+00:00",
                "intersection_id": "int-001",
                "current_green_seconds": 45,
                "recommended_green_seconds": 60,
                "delta_seconds": 15,
                "reason": "High predicted congestion on northbound lane",
                "congestion_risk_percent": 78.5,
            }
        },
    )

    intersection_id: str = Field(description="Target intersection identifier")
    current_green_seconds: int = Field(
        ge=5,
        strict=True,
        description="Current green-light duration in seconds",
    )
    recommended_green_seconds: int = Field(
        ge=5,
        strict=True,
        description="Recommended green-light duration in seconds",
    )
    delta_seconds: int = Field(
        strict=True,
        description="Difference from current to recommended duration",
    )
    reason: str = Field(description="Human-readable recommendation reason")
    congestion_risk_percent: float = Field(
        ge=0.0,
        le=100.0,
        strict=True,
        description="Congestion risk percentage from 0 to 100",
    )


class NotificationSchema(BaseModel):
    """Notification payload contract for dashboard consumers.

    Attributes:
        id: Stable notification identifier.
        level: Notification severity level.
        title: Short notification title.
        description: Detailed notification message.
        timestamp: ISO-8601 UTC notification timestamp.
        intersection_id: Related intersection identifier.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "notif-001",
                "level": "WARNING",
                "title": "Congestion risk rising",
                "description": "Intersection 1 is approaching high density.",
                "timestamp": "2026-05-27T22:37:00+00:00",
                "intersection_id": "int-001",
            }
        },
    )

    id: str = Field(description="Stable notification identifier")
    level: Literal["INFO", "WARNING", "CRITICAL"] = Field(
        description="Notification severity level",
    )
    title: str = Field(description="Short notification title")
    description: str = Field(description="Detailed notification message")
    timestamp: str = Field(description="ISO-8601 UTC notification timestamp")
    intersection_id: str = Field(description="Related intersection identifier")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate notification timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class ErrorResponse(BaseModel):
    """Simple API error response contract.

    Attributes:
        success: Whether the request completed successfully.
        error_code: Stable machine-readable error code.
        detail: Human-readable error detail.
        timestamp: ISO-8601 UTC error timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "detail": "Request validation failed",
                "timestamp": "2026-05-27T22:37:00+00:00",
            }
        },
    )

    success: bool = Field(description="Whether the request was successful")
    error_code: str = Field(description="Stable machine-readable error code")
    detail: str = Field(description="Human-readable error detail")
    timestamp: str = Field(description="ISO-8601 UTC error timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate error timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class ErrorDetail(BaseModel):
    """Standardized envelope error detail schema.

    Attributes:
        code: Stable machine-readable error code.
        message: Human-readable error message.
        details: Structured frontend-safe error details.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [{"field": "horizon", "reason": "Invalid value"}],
            }
        },
    )

    code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Human-readable error message")
    details: list[JsonFlatObject] | list[JsonPrimitive] = Field(
        default_factory=list,
        description="Structured frontend-safe error details",
    )


class StandardSuccessResponse(BaseModel):
    """Standardized API success envelope schema.

    Attributes:
        success: Whether the request completed successfully.
        message: Human-readable response message.
        data: Frontend-safe JSON response payload.
        request_id: Request tracing identifier.
        timestamp: ISO-8601 UTC response timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "pong",
                "data": {"alive": True},
                "request_id": "req_a1b2c3d4",
                "timestamp": "2026-05-27T22:37:00+00:00",
            }
        },
    )

    success: bool = Field(description="Whether the request was successful")
    message: str = Field(description="Human-readable response message")
    data: JsonPayload = Field(
        description="Frontend-safe JSON response payload",
    )
    request_id: str = Field(description="Request tracing identifier")
    timestamp: str = Field(description="ISO-8601 UTC response timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate response timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class StandardErrorResponse(BaseModel):
    """Standardized API error envelope schema.

    Attributes:
        success: Whether the request completed successfully.
        error: Error detail payload.
        request_id: Request tracing identifier.
        timestamp: ISO-8601 UTC error timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": [],
                },
                "request_id": "req_a1b2c3d4",
                "timestamp": "2026-05-27T22:37:00+00:00",
            }
        },
    )

    success: bool = Field(description="Whether the request was successful")
    error: ErrorDetail = Field(description="Error detail payload")
    request_id: str = Field(description="Request tracing identifier")
    timestamp: str = Field(description="ISO-8601 UTC error timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate error timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class HealthResponse(BaseModel):
    """Health check response schema kept for compatibility.

    Attributes:
        service: Service name.
        version: Service semantic version.
        status: Liveness status.
        environment: Runtime environment.
        ml_horizons_supported: Supported ML prediction horizons.
        timestamp: ISO-8601 UTC health-check timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "service": "traffix-backend",
                "version": "0.1.0",
                "status": "ok",
                "environment": "development",
                "ml_horizons_supported": ["15m", "2h", "4h"],
                "timestamp": "2026-05-27T22:37:00+00:00",
            }
        },
    )

    service: str = Field(description="Service name")
    version: str = Field(description="Service semantic version")
    status: str = Field(description="Liveness status")
    environment: str = Field(description="Runtime environment")
    ml_horizons_supported: list[Literal["15m", "2h", "4h"]] = Field(
        description="Supported ML prediction horizons",
    )
    timestamp: str = Field(description="ISO-8601 UTC timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate health-check timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class PingResponse(BaseModel):
    """Connectivity check response schema kept for compatibility.

    Attributes:
        success: Whether ping succeeded.
        message: Ping response message.
        timestamp: ISO-8601 UTC ping timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "success": True,
                "message": "pong",
                "timestamp": "2026-05-27T22:37:00+00:00",
            }
        },
    )

    success: bool = Field(description="Whether ping succeeded")
    message: str = Field(description="Ping response message")
    timestamp: str = Field(description="ISO-8601 UTC timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate ping timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class VersionResponse(BaseModel):
    """Backend version metadata schema kept for compatibility.

    Attributes:
        service: Service name.
        version: Service semantic version.
        api_version: API version label.
        environment: Runtime environment.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "service": "traffix-backend",
                "version": "0.1.0",
                "api_version": "v1",
                "environment": "development",
            }
        },
    )

    service: str = Field(description="Service name")
    version: str = Field(description="Service semantic version")
    api_version: Literal["v1"] = Field(description="API version label")
    environment: str = Field(description="Runtime environment")


class SystemStatusResponse(BaseModel):
    """Runtime capability status schema kept for compatibility.

    Attributes:
        service: Service name.
        status: Runtime status.
        ml_ready: Whether ML inference is ready.
        weather_ready: Whether weather integration is ready.
        simulation_ready: Whether simulation is ready.
        camera_ready: Whether camera input is ready.
        supported_horizons: Supported ML prediction horizons.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "service": "traffix-backend",
                "status": "operational",
                "ml_ready": False,
                "weather_ready": False,
                "simulation_ready": False,
                "camera_ready": False,
                "supported_horizons": ["15m", "2h", "4h"],
            }
        },
    )

    service: str = Field(description="Service name")
    status: Literal["operational"] = Field(description="Runtime status")
    ml_ready: bool = Field(description="Whether ML inference is ready")
    weather_ready: bool = Field(description="Whether weather integration is ready")
    simulation_ready: bool = Field(description="Whether simulation is ready")
    camera_ready: bool = Field(description="Whether camera input is ready")
    supported_horizons: list[Literal["15m", "2h", "4h"]] = Field(
        description="Supported ML prediction horizons",
    )


class SystemRuntimeStatusResponse(BaseModel):
    """System runtime status response for the modular system router.

    Attributes:
        service: Service name.
        status: Runtime status.
        ml_models_loaded: Whether ML model artifacts are loaded.
        simulation_active: Whether the simulation loop is active.
        weather_service: Current weather service lifecycle state.
        timestamp: ISO-8601 UTC status timestamp.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "service": "traffix-backend",
                "status": "operational",
                "ml_models_loaded": False,
                "simulation_active": False,
                "weather_service": "standby",
                "timestamp": "2026-05-27T22:45:00+00:00",
            }
        },
    )

    service: str = Field(description="Service name")
    status: Literal["operational"] = Field(description="Runtime status")
    ml_models_loaded: bool = Field(
        description="Whether ML model artifacts are loaded",
    )
    simulation_active: bool = Field(
        description="Whether the simulation loop is active",
    )
    weather_service: Literal["standby", "active", "unavailable"] = Field(
        description="Current weather service lifecycle state",
    )
    timestamp: str = Field(description="ISO-8601 UTC status timestamp")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        """Validate status timestamp.

        Args:
            value: Timestamp string to validate.

        Returns:
            Validated timestamp string.
        """
        return _validate_utc_iso_timestamp(value)


class SystemTimeResponse(BaseModel):
    """System time response for Asia/Jakarta timezone.

    Attributes:
        timezone: IANA timezone name.
        current_time_wib: Formatted WIB local time.
        unix: Unix timestamp in seconds.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "timezone": "Asia/Jakarta",
                "current_time_wib": "2026-05-27 22:45:00 WIB",
                "unix": 1770000000,
            }
        },
    )

    timezone: Literal["Asia/Jakarta"] = Field(description="IANA timezone name")
    current_time_wib: str = Field(description="Formatted WIB local time")
    unix: int = Field(ge=0, strict=True, description="Unix timestamp")


class SystemVersionInfoResponse(BaseModel):
    """System version response for the modular system router.

    Attributes:
        app_name: Application name.
        version: Application semantic version.
        environment: Runtime environment.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "app_name": "traffix-backend",
                "version": "0.1.0",
                "environment": "development",
            }
        },
    )

    app_name: str = Field(description="Application name")
    version: str = Field(description="Application semantic version")
    environment: str = Field(description="Runtime environment")
