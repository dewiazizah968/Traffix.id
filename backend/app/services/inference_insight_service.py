"""Bridge LSTM/YOLO inference artifacts to dashboard intersection APIs."""

from __future__ import annotations

from typing import Any

from app.services.camera_service import camera_service
from app.state_store import state_store

InsightPayload = dict[str, Any]


class InferenceInsightService:
    """Resolve data-team inference fields for live dashboard intersections."""

    def get_insight(self, intersection_id: str) -> InsightPayload | None:
        """Return LSTM insight fields for one dashboard intersection.

        Args:
            intersection_id: Live-state intersection identifier such as INT-001.

        Returns:
            Inference insight payload when a matching camera row exists.
        """
        normalized_id = intersection_id.upper()
        state = state_store.get_state(normalized_id)
        if state is None:
            return None

        camera = self._camera_for_intersection_name(state["intersection_name"])
        if camera is None:
            return None

        traffic = camera.get("traffic") or {}
        predictions = camera.get("predictions") or {}
        green_seconds = traffic.get("green_seconds")
        congestion_level = traffic.get("congestion_level")
        return {
            "source": camera.get("prediction_source") or "inference-output",
            "camera_id": camera.get("camera_id"),
            "intersection_name": camera.get("intersection_name"),
            "ai_insight": camera.get("ai_insight"),
            "recommendation": camera.get("recommendation"),
            "recommended_green_seconds": green_seconds,
            "current_green_seconds": green_seconds,
            "congestion_level": congestion_level,
            "traffic": traffic,
            "predictions": predictions,
            "model_mape": camera.get("model_mape"),
            "dashboard_priority": self._dashboard_priority(congestion_level),
            "display_recommendation": bool(
                camera.get("ai_insight") or camera.get("recommendation"),
            ),
        }

    def get_all_insights(self) -> dict[str, InsightPayload]:
        """Return inference insights keyed by intersection ID."""
        insights: dict[str, InsightPayload] = {}
        for intersection_id in state_store.get_intersection_ids():
            insight = self.get_insight(intersection_id)
            if insight is not None:
                insights[intersection_id] = insight
        return insights

    def _camera_for_intersection_name(
        self,
        intersection_name: str,
    ) -> dict[str, Any] | None:
        """Find the latest camera payload for a dashboard intersection name."""
        target = intersection_name.strip().casefold()
        for camera in camera_service.list_cameras():
            name = str(camera.get("intersection_name") or "").strip().casefold()
            if name == target:
                return camera
        return None

    def _dashboard_priority(self, congestion_level: str | None) -> str:
        """Map congestion labels to dashboard display priority."""
        normalized = (congestion_level or "").strip().casefold()
        if normalized in {"severe", "high"}:
            return "high"
        if normalized == "medium":
            return "medium"
        return "low"


inference_insight_service = InferenceInsightService()
