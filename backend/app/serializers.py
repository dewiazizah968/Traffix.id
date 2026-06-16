"""Serialize live runtime state for Traffix API responses."""

from app.services.inference_insight_service import inference_insight_service
from app.state_store import LiveIntersectionState


def serialize_live_intersection(state: LiveIntersectionState) -> dict[str, object]:
    """Convert a live intersection state into an API payload.

    Args:
        state: Live intersection snapshot.

    Returns:
        JSON-serializable intersection payload.
    """
    insight = inference_insight_service.get_insight(state["intersection_id"])
    payload: dict[str, object] = {
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
        "ai_insight": None,
        "recommendation": None,
        "recommended_green_seconds": None,
        "congestion_level": None,
        "inference_source": None,
        "dashboard_priority": "low",
        "display_recommendation": False,
    }
    if insight is not None:
        payload.update(
            {
                "ai_insight": insight.get("ai_insight"),
                "recommendation": insight.get("recommendation"),
                "recommended_green_seconds": insight.get("recommended_green_seconds"),
                "congestion_level": insight.get("congestion_level"),
                "inference_source": insight.get("source"),
                "dashboard_priority": insight.get("dashboard_priority"),
                "display_recommendation": insight.get("display_recommendation"),
            },
        )
        lstm_predictions = insight.get("predictions")
        if isinstance(lstm_predictions, dict) and lstm_predictions:
            payload["ai_predictions"] = {
                **state["ai_predictions"],
                **lstm_predictions,
            }
    return payload
