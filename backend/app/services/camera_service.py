"""Camera and YOLO readiness service."""

from __future__ import annotations

from datetime import datetime, timezone

from app.state_store import state_store
from core.config import settings


class CameraService:
    """Expose camera/YOLO integration readiness without side effects."""

    def status(self) -> dict[str, object]:
        """Return camera and YOLO runtime status.

        Returns:
            Serializable camera status payload.
        """
        cameras = self.list_cameras()
        return {
            "camera_input_enabled": settings.camera_input_enabled,
            "max_cameras": settings.max_cameras,
            "configured_cameras": len(cameras),
            "active_cameras": sum(1 for camera in cameras if camera["status"] == "active"),
            "yolo_ready": False,
            "model_loaded": False,
            "mode": "standby" if not settings.camera_input_enabled else "configured",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "message": (
                "Camera input is disabled; YOLO pipeline can be attached via future stream adapters."
                if not settings.camera_input_enabled
                else "Camera input is enabled; attach stream URLs to activate detection."
            ),
        }

    def list_cameras(self) -> list[dict[str, object]]:
        """Return deterministic camera slots for live intersections.

        Returns:
            Camera slot payloads.
        """
        cameras: list[dict[str, object]] = []
        for index, intersection in enumerate(state_store.get_all_states(), start=1):
            if index > settings.max_cameras:
                break
            cameras.append(
                {
                    "camera_id": f"CAM-{index:03d}",
                    "intersection_id": intersection["intersection_id"],
                    "intersection_name": intersection["intersection_name"],
                    "status": "standby" if settings.camera_input_enabled else "disabled",
                    "stream_url": None,
                    "last_frame_at": None,
                    "detected_vehicle_count": intersection["vehicle_count"],
                    "source": "simulation-state",
                },
            )
        return cameras


camera_service = CameraService()
