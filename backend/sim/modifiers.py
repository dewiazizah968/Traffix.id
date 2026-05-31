"""Pure traffic modifier functions for simulation realism."""

from dataclasses import dataclass, replace
from datetime import datetime


@dataclass(frozen=True)
class TrafficSnapshot:
    """Traffic values used by the congestion modifier engine."""

    vehicle_count: int
    avg_speed: float
    occupancy_rate: float
    queue_length: int
    weather_condition: str
    timestamp: datetime


def clamp_float(value: float, minimum: float, maximum: float) -> float:
    """Clamp a float into a safe range.

    Args:
        value: Input value.
        minimum: Minimum allowed value.
        maximum: Maximum allowed value.

    Returns:
        Clamped float value.
    """
    return max(minimum, min(maximum, value))


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    """Clamp an integer into a safe range.

    Args:
        value: Input value.
        minimum: Minimum allowed value.
        maximum: Maximum allowed value.

    Returns:
        Clamped integer value.
    """
    return max(minimum, min(maximum, value))


def is_rush_hour(timestamp: datetime) -> bool:
    """Return whether a timestamp falls inside rush-hour windows.

    Args:
        timestamp: Dataset timestamp.

    Returns:
        True for 07:00-09:00 or 16:00-19:00.
    """
    hour = timestamp.hour
    return 7 <= hour < 9 or 16 <= hour < 19


def apply_rush_hour_modifier(snapshot: TrafficSnapshot) -> TrafficSnapshot:
    """Apply deterministic rush-hour congestion effects.

    Args:
        snapshot: Input traffic snapshot.

    Returns:
        Modified traffic snapshot.
    """
    if not is_rush_hour(snapshot.timestamp):
        return snapshot

    return replace(
        snapshot,
        vehicle_count=clamp_int(round(snapshot.vehicle_count * 1.25), 0, 300),
        avg_speed=clamp_float(snapshot.avg_speed * 0.85, 1.0, 120.0),
    )


def apply_weather_modifier(snapshot: TrafficSnapshot) -> TrafficSnapshot:
    """Apply deterministic weather-based traffic effects.

    Args:
        snapshot: Input traffic snapshot.

    Returns:
        Modified traffic snapshot.
    """
    if snapshot.weather_condition.strip().lower() != "rain":
        return snapshot

    return replace(
        snapshot,
        avg_speed=clamp_float(snapshot.avg_speed * 0.80, 1.0, 120.0),
        occupancy_rate=clamp_float(snapshot.occupancy_rate * 1.10, 0.0, 1.0),
        queue_length=clamp_int(round(snapshot.queue_length * 1.15), 0, 250),
    )


def apply_queue_buildup_modifier(snapshot: TrafficSnapshot) -> TrafficSnapshot:
    """Apply natural queue buildup from density and speed pressure.

    Args:
        snapshot: Input traffic snapshot.

    Returns:
        Modified traffic snapshot.
    """
    pressure = snapshot.occupancy_rate
    speed_penalty = 1.0 if snapshot.avg_speed < 20 else 0.0
    buildup = round(snapshot.vehicle_count * pressure * 0.08 + speed_penalty)

    return replace(
        snapshot,
        queue_length=clamp_int(snapshot.queue_length + buildup, 0, 250),
    )


def apply_speed_degradation_modifier(snapshot: TrafficSnapshot) -> TrafficSnapshot:
    """Apply speed degradation from occupancy and queue pressure.

    Args:
        snapshot: Input traffic snapshot.

    Returns:
        Modified traffic snapshot.
    """
    occupancy_penalty = snapshot.occupancy_rate * 0.12
    queue_penalty = min(snapshot.queue_length / 200, 0.18)
    multiplier = 1.0 - occupancy_penalty - queue_penalty

    return replace(
        snapshot,
        avg_speed=clamp_float(snapshot.avg_speed * multiplier, 1.0, 120.0),
    )


def clamp_snapshot(snapshot: TrafficSnapshot) -> TrafficSnapshot:
    """Clamp all traffic values to safe simulation ranges.

    Args:
        snapshot: Input traffic snapshot.

    Returns:
        Safely clamped traffic snapshot.
    """
    return replace(
        snapshot,
        vehicle_count=clamp_int(snapshot.vehicle_count, 0, 300),
        avg_speed=clamp_float(snapshot.avg_speed, 1.0, 120.0),
        occupancy_rate=clamp_float(snapshot.occupancy_rate, 0.0, 1.0),
        queue_length=clamp_int(snapshot.queue_length, 0, 250),
    )
