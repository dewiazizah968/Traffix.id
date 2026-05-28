"""Serialize live runtime state for Traffix API responses."""

from app.state_store import LiveIntersectionState


def serialize_live_intersection(state: LiveIntersectionState) -> dict[str, object]:
    """Convert a live intersection state into an API payload.

    Args:
        state: Live intersection snapshot.

    Returns:
        JSON-serializable intersection payload.
    """
    return {
        "intersection_id": state["intersection_id"],
        "intersection_name": state["intersection_name"],
        "vehicle_count": state["vehicle_count"],
        "avg_speed": state["avg_speed"],
        "occupancy_rate": state["occupancy_rate"],
        "queue_length": state["queue_length"],
        "signal_state": state["signal_state"],
        "green_duration_seconds": state["green_duration_seconds"],
        "weather_condition": state["weather_condition"],
        "ai_predictions": state["ai_predictions"],
        "last_updated": state["last_updated"],
    }
