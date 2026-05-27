"""Pydantic models for hybrid traffic dataset ingestion."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatasetRow(BaseModel):
    """Typed row from `hybrid_traffic_7d.csv`.

    Attributes:
        timestamp: Timezone-aware UTC observation timestamp.
        intersection_id: Intersection identifier from the dataset.
        vehicle_count: Number of vehicles observed in the interval.
        avg_speed: Average vehicle speed in kilometers per hour.
        occupancy_rate: Lane occupancy ratio from 0 to 1.
        queue_length: Number of queued vehicles.
        weather_condition: Weather condition label.
        temperature_celsius: Ambient temperature in Celsius.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "timestamp": "2026-05-27T22:52:00+00:00",
                "intersection_id": "INT-001",
                "vehicle_count": 42,
                "avg_speed": 31.5,
                "occupancy_rate": 0.72,
                "queue_length": 18,
                "weather_condition": "Rain",
                "temperature_celsius": 27.5,
            }
        },
    )

    timestamp: datetime = Field(description="UTC observation timestamp")
    intersection_id: str = Field(description="Intersection identifier")
    vehicle_count: int = Field(
        ge=0,
        strict=True,
        description="Number of vehicles observed in the interval",
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
    weather_condition: str = Field(description="Weather condition label")
    temperature_celsius: float = Field(
        strict=True,
        description="Ambient temperature in Celsius",
    )
    target_volume_15m: float | None = Field(
        default=None,
        description="Data team 15-minute target volume for ML fallback",
    )
    target_volume_2h: float | None = Field(
        default=None,
        description="Data team 2-hour target volume for ML fallback",
    )
    target_volume_4h: float | None = Field(
        default=None,
        description="Data team 4-hour target volume for ML fallback",
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        """Validate timestamp is timezone-aware UTC.

        Args:
            value: Parsed observation timestamp.

        Returns:
            UTC-normalized timestamp.

        Raises:
            ValueError: If timestamp is not timezone-aware.
        """
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(timezone.utc)


class DatasetMetadata(BaseModel):
    """Summary metadata for a loaded hybrid traffic dataset.

    Attributes:
        rows: Number of rows in the dataset.
        intersections: Number of unique intersections.
        start_time: Earliest UTC timestamp in the dataset.
        end_time: Latest UTC timestamp in the dataset.
        time_resolution_minutes: Median timestamp interval in minutes.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "rows": 672,
                "intersections": 4,
                "start_time": "2026-05-27T00:00:00+00:00",
                "end_time": "2026-06-02T23:45:00+00:00",
                "time_resolution_minutes": 15,
            }
        },
    )

    rows: int = Field(ge=0, strict=True, description="Number of dataset rows")
    intersections: int = Field(
        ge=0,
        strict=True,
        description="Number of unique intersections",
    )
    start_time: datetime | None = Field(
        default=None,
        description="Earliest UTC timestamp in the dataset",
    )
    end_time: datetime | None = Field(
        default=None,
        description="Latest UTC timestamp in the dataset",
    )
    time_resolution_minutes: int = Field(
        ge=0,
        strict=True,
        description="Median timestamp interval in minutes",
    )
