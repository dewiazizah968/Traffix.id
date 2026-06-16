"""Camera and YOLO readiness service."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.state_store import state_store
from core.config import settings
from core.paths import resolve_asset_path

VIDEO_ROUTE_PREFIX = "/api/v1/cameras/videos"
PredictionRow = dict[str, Any]


class CameraService:
    """Expose camera/YOLO integration readiness without side effects."""

    def status(self) -> dict[str, object]:
        """Return camera and YOLO runtime status.

        Returns:
            Serializable camera status payload.
        """
        cameras = self.list_cameras()
        videos_available = sum(1 for camera in cameras if camera.get("video_exists"))
        predictions_available = sum(
            1 for camera in cameras if camera.get("prediction_source")
        )
        metadata_loaded = self.metadata_path.exists()
        yolo_output_loaded = self.yolo_vehicle_count_path.exists()
        frontend_ready = metadata_loaded and (
            predictions_available > 0 or yolo_output_loaded
        )
        warnings: list[str] = []
        if not metadata_loaded:
            warnings.append("CCTV metadata CSV is missing")
        if predictions_available == 0:
            warnings.append("LSTM prediction output is missing or not matched to cameras")
        if videos_available == 0 and cameras:
            warnings.append(
                "Camera MP4 files are not present in backend video storage; "
                "use video_library_url or frontend placeholders",
            )

        return {
            "camera_input_enabled": settings.camera_input_enabled,
            "max_cameras": settings.max_cameras,
            "configured_cameras": len(cameras),
            "active_cameras": sum(1 for camera in cameras if camera["status"] == "active"),
            "api_ready_cameras": len(cameras) if frontend_ready else 0,
            "videos_available": videos_available,
            "videos_missing": len(cameras) - videos_available,
            "predictions_available": predictions_available,
            "metadata_loaded": metadata_loaded,
            "prediction_output_loaded": self.prediction_output_available,
            "prediction_output_source": self.prediction_output_source,
            "yolo_output_loaded": yolo_output_loaded,
            "yolo_output_source": "csv" if yolo_output_loaded else None,
            "video_library_url": settings.camera_video_library_url,
            "video_storage_path": str(self.video_root_path),
            "frontend_ready": frontend_ready,
            "warnings": warnings,
            "data_sources": {
                "metadata": {
                    "loaded": metadata_loaded,
                    "path": str(self.metadata_path),
                },
                "lstm_predictions": {
                    "loaded": self.prediction_output_available,
                    "source": self.prediction_output_source,
                    "path": str(
                        self.prediction_output_json_path
                        if self.prediction_output_json_path.exists()
                        else self.prediction_output_path
                    ),
                },
                "yolo_vehicle_counts": {
                    "loaded": yolo_output_loaded,
                    "source": "csv" if yolo_output_loaded else None,
                    "path": str(self.yolo_vehicle_count_path),
                },
                "videos": {
                    "available": videos_available,
                    "missing": len(cameras) - videos_available,
                    "storage_path": str(self.video_root_path),
                    "library_url": settings.camera_video_library_url,
                },
            },
            "yolo_ready": metadata_loaded and yolo_output_loaded,
            "model_loaded": False,
            "mode": (
                "metadata"
                if metadata_loaded
                else "standby" if not settings.camera_input_enabled else "configured"
            ),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "message": (
                "Validated CCTV metadata, LSTM predictions, and YOLO counts are ready for the frontend."
                if frontend_ready
                else (
                    "Camera input is disabled; YOLO pipeline can be attached via future stream adapters."
                    if not settings.camera_input_enabled
                    else "Camera input is enabled; attach stream URLs to activate detection."
                )
            ),
        }

    @property
    def metadata_path(self) -> Path:
        """Return the resolved CCTV metadata CSV path."""
        return resolve_asset_path(settings.camera_metadata_path)

    @property
    def video_root_path(self) -> Path:
        """Return the resolved backend-hosted CCTV video root path."""
        return resolve_asset_path(settings.camera_video_root_path)

    @property
    def prediction_output_path(self) -> Path:
        """Return the resolved LSTM video prediction output CSV path."""
        return resolve_asset_path(settings.prediction_output_path)

    @property
    def prediction_output_json_path(self) -> Path:
        """Return the resolved LSTM video prediction output JSON path."""
        return resolve_asset_path(settings.prediction_output_json_path)

    @property
    def yolo_vehicle_count_path(self) -> Path:
        """Return the resolved YOLO vehicle count CSV path."""
        return resolve_asset_path(settings.yolo_vehicle_count_path)

    @property
    def prediction_output_available(self) -> bool:
        """Return whether a LSTM prediction output file is available."""
        return self.prediction_output_json_path.exists() or self.prediction_output_path.exists()

    @property
    def prediction_output_source(self) -> str | None:
        """Return the active prediction output source type."""
        if self.prediction_output_json_path.exists():
            return "json"
        if self.prediction_output_path.exists():
            return "csv"
        return None

    def list_cameras(self) -> list[dict[str, object]]:
        """Return deterministic camera slots for live intersections.

        Returns:
            Camera slot payloads.
        """
        metadata_cameras = self._list_metadata_cameras()
        if metadata_cameras:
            return metadata_cameras

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

    def resolve_video_path(self, period: str, filename: str) -> Path | None:
        """Resolve a requested video filename inside the configured video root."""
        if not filename.lower().endswith(".mp4"):
            return None

        root = self.video_root_path.resolve()
        candidate = (root / period / filename).resolve()
        if root not in candidate.parents or not candidate.exists():
            return None
        return candidate

    def _list_metadata_cameras(self) -> list[dict[str, object]]:
        """Build camera API rows from validated CCTV metadata."""
        path = self.metadata_path
        if not path.exists():
            return []

        predictions_by_video = self._load_prediction_outputs()
        yolo_by_video = self._load_yolo_outputs()
        latest_by_camera: dict[str, dict[str, str]] = {}
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            for row in csv.DictReader(csv_file):
                camera_id = (row.get("camera_id") or row.get("cctv_id") or "").strip()
                if not camera_id:
                    continue
                current = latest_by_camera.get(camera_id)
                video_file = (row.get("video_file") or "").strip()
                current_video = (
                    (current.get("video_file") or "").strip()
                    if current is not None
                    else ""
                )
                row_has_data = (
                    video_file in predictions_by_video or video_file in yolo_by_video
                )
                current_has_data = (
                    current_video in predictions_by_video
                    or current_video in yolo_by_video
                )
                if (
                    current is None
                    or (row_has_data and not current_has_data)
                    or (
                        row_has_data == current_has_data
                        and row.get("timestamp_wib", "") > current.get("timestamp_wib", "")
                    )
                ):
                    latest_by_camera[camera_id] = row

        cameras: list[dict[str, object]] = []
        for row in sorted(latest_by_camera.values(), key=lambda item: item.get("camera_id", "")):
            if len(cameras) >= settings.max_cameras:
                break
            prediction_row = predictions_by_video.get((row.get("video_file") or "").strip())
            yolo_row = yolo_by_video.get((row.get("video_file") or "").strip())
            cameras.append(self._camera_from_metadata(row, prediction_row, yolo_row))
        return cameras

    def _load_prediction_outputs(self) -> dict[str, PredictionRow]:
        """Load latest LSTM prediction rows keyed by source video filename."""
        json_predictions = self._load_prediction_outputs_from_json()
        if json_predictions:
            return json_predictions
        return self._load_prediction_outputs_from_csv()

    def _load_prediction_outputs_from_json(self) -> dict[str, PredictionRow]:
        """Load LSTM prediction rows from the inference JSON artifact."""
        path = self.prediction_output_json_path
        if not path.exists():
            return {}

        with path.open("r", encoding="utf-8") as json_file:
            payload = json.load(json_file)

        if not isinstance(payload, list):
            return {}

        predictions: dict[str, PredictionRow] = {}
        for item in payload:
            if not isinstance(item, dict):
                continue
            source_video = str(item.get("source_video") or "").strip()
            if source_video:
                predictions[source_video] = item
        return predictions

    def _load_prediction_outputs_from_csv(self) -> dict[str, PredictionRow]:
        """Load LSTM prediction rows from the CSV artifact as a fallback."""
        path = self.prediction_output_path
        if not path.exists():
            return {}

        predictions: dict[str, PredictionRow] = {}
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            for row in csv.DictReader(csv_file):
                source_video = (row.get("source_video") or "").strip()
                if source_video:
                    predictions[source_video] = row
        return predictions

    def _load_yolo_outputs(self) -> dict[str, PredictionRow]:
        """Load YOLO vehicle-count rows keyed by source video filename."""
        path = self.yolo_vehicle_count_path
        if not path.exists():
            return {}

        detections: dict[str, PredictionRow] = {}
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            for row in csv.DictReader(csv_file):
                source_video = (row.get("source_video") or "").strip()
                if source_video:
                    detections[source_video] = row
        return detections

    def _camera_from_metadata(
        self,
        row: dict[str, str],
        prediction_row: PredictionRow | None,
        yolo_row: PredictionRow | None,
    ) -> dict[str, object]:
        """Convert one metadata row into the frontend camera payload."""
        camera_id = (row.get("camera_id") or row.get("cctv_id") or "").strip()
        period = (row.get("period") or row.get("period_from_filename") or "").strip()
        video_file = (row.get("video_file") or "").strip()
        camera_label = (
            row.get("camera_label")
            or row.get("location_text")
            or row.get("km_text")
            or camera_id
        ).strip()
        expected_video_url = self._video_url(period, video_file)
        video_exists = (
            self.resolve_video_path(period, video_file) is not None
            if period and video_file
            else False
        )
        video_url = expected_video_url if video_exists else None
        detected_vehicle_count = self._optional_int(
            self._prediction_value(prediction_row, "vehicle_count"),
        )
        if detected_vehicle_count is None:
            detected_vehicle_count = self._optional_int(
                self._prediction_value(yolo_row, "vehicle_count"),
            )

        data_sources = ["validated-cctv-metadata"]
        if prediction_row is not None:
            data_sources.append(
                "lstm-output-json"
                if self.prediction_output_json_path.exists()
                else "lstm-output-csv",
            )
        if yolo_row is not None:
            data_sources.append("yolo-vehicle-count-csv")
        if video_exists:
            data_sources.append("backend-video-storage")

        payload: dict[str, object] = {
            "camera_id": camera_id,
            "intersection_id": row.get("camera_key") or camera_id,
            "intersection_name": camera_label,
            "status": "active" if video_exists else "metadata-only",
            "stream_url": video_url,
            "video_url": video_url,
            "expected_video_url": expected_video_url,
            "video_file": video_file or None,
            "video_exists": video_exists,
            "video_placeholder_required": not video_exists,
            "video_status": "ready" if video_exists else "missing",
            "video_format_hint": "Browser-safe MP4 (H.264 video, AAC audio)",
            "video_library_url": settings.camera_video_library_url,
            "recorded_at": row.get("timestamp_wib") or None,
            "period": period or None,
            "ruas": row.get("ruas") or None,
            "location_type": row.get("location_type") or None,
            "km_text": row.get("km_text") or None,
            "latitude": self._optional_float(row.get("lat")),
            "longitude": self._optional_float(row.get("lon")),
            "last_frame_at": row.get("timestamp_wib") or None,
            "detected_vehicle_count": detected_vehicle_count,
            "data_sources": data_sources,
            "source": "+".join(data_sources),
        }
        if prediction_row is not None:
            payload.update(self._prediction_payload(prediction_row))
        if yolo_row is not None:
            payload["yolo"] = self._yolo_payload(yolo_row)
            if "traffic" not in payload:
                payload["traffic"] = self._traffic_payload(yolo_row)
        return payload

    def _video_url(self, period: str, video_file: str) -> str | None:
        """Build the backend API URL for a video file."""
        if not period or not video_file:
            return None
        return f"{VIDEO_ROUTE_PREFIX}/{quote(period)}/{quote(video_file)}"

    def _optional_float(self, value: Any) -> float | None:
        """Parse optional float metadata values."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _optional_int(self, value: Any) -> int | None:
        """Parse optional integer metadata values."""
        parsed = self._optional_float(value)
        if parsed is None:
            return None
        return int(round(parsed))

    def _prediction_value(
        self,
        prediction_row: PredictionRow | None,
        key: str,
    ) -> Any:
        """Read a raw value from an optional prediction row."""
        if prediction_row is None:
            return None
        return prediction_row.get(key)

    def _prediction_payload(self, row: PredictionRow) -> dict[str, object]:
        """Build frontend-ready prediction fields from LSTM inference output."""
        return {
            "prediction_source": "lstm-output-json"
            if self.prediction_output_json_path.exists()
            else "lstm-output-csv",
            "traffic": self._traffic_payload(row),
            "predictions": {
                "15m": self._optional_float(row.get("predicted_volume_15m")),
                "2h": self._optional_float(row.get("predicted_volume_2h")),
                "4h": self._optional_float(row.get("predicted_volume_4h")),
            },
            "model_mape": {
                "15m": self._optional_float(row.get("model_mape_15m")),
                "2h": self._optional_float(row.get("model_mape_2h")),
                "4h": self._optional_float(row.get("model_mape_4h")),
            },
            "ai_insight": row.get("ai_insight") or None,
            "recommendation": row.get("recommendation") or None,
        }

    def _traffic_payload(self, row: PredictionRow) -> dict[str, object]:
        """Build traffic fields shared by LSTM and YOLO outputs."""
        return {
            "vehicle_count": self._optional_int(row.get("vehicle_count")),
            "vehicle_count_1min": self._optional_int(row.get("vehicle_count_1min")),
            "volume_veh_per_hour": self._optional_float(row.get("volume_veh_per_hour")),
            "avg_speed_kmh": self._optional_float(row.get("avg_speed_kmh")),
            "density_percent": self._optional_float(row.get("density_percent")),
            "queue_length_veh": self._optional_int(row.get("queue_length_veh")),
            "green_seconds": self._optional_float(row.get("green_seconds")),
            "congestion_level": row.get("congestion_level") or None,
            "weather": row.get("weather") or None,
            "weather_temp_c": self._optional_float(row.get("weather_temp_c")),
        }

    def _yolo_payload(self, row: PredictionRow) -> dict[str, object]:
        """Build frontend-ready YOLO detection metadata."""
        return {
            "source": "yolo-vehicle-count-csv",
            "source_video": row.get("source_video") or None,
            "detected_video_path": row.get("detected_video_path") or None,
            "traffic": self._traffic_payload(row),
        }


camera_service = CameraService()
