"""Traffix prediction service with Keras and dataset fallback modes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from app.state_store import LiveIntersectionState, state_store
from core.constants import HORIZONS
from core.logger import get_logger
from ml import preprocess
from ml.model_loader import (
    get_model,
    get_scalers,
    ml_fallback_active,
    models_loaded,
)
from ml.registry import registry
from sim.dataset_models import DatasetRow

ml_logger = get_logger("ml")

CongestionLevel = Literal["Low", "Medium", "High", "Critical"]

HORIZON_VOLUME_SCALE = {
    "15m": 1.0,
    "2h": 1.35,
    "4h": 1.75,
}


@dataclass(frozen=True)
class PredictionResult:
    """Structured prediction output for API and state store updates."""

    intersection_id: str
    horizon: str
    predicted_vehicle_count: int
    predicted_congestion_level: CongestionLevel
    confidence_score: float
    prediction_timestamp: str
    source: Literal["lstm", "dataset", "heuristic"]


class PredictionService:
    """Generate multi-horizon predictions and sync them to live state."""

    def __init__(self) -> None:
        """Initialize prediction caches."""
        self._latest_rows: dict[str, DatasetRow] = {}

    def note_dataset_batch(self, rows: list[DatasetRow]) -> None:
        """Cache the latest dataset row per intersection from a replay batch.

        Args:
            rows: Dataset rows processed in the current tick.
        """
        for row in rows:
            self._latest_rows[row.intersection_id] = row

    def predict(
        self,
        intersection_id: str,
        horizon: str,
    ) -> PredictionResult:
        """Generate a prediction for one intersection and horizon.

        Args:
            intersection_id: Target intersection identifier.
            horizon: Prediction horizon.

        Returns:
            Structured prediction result.
        """
        if horizon not in HORIZONS:
            raise ValueError(f"Unsupported horizon: {horizon}")

        live_state = state_store.get_state(intersection_id)
        if live_state is None:
            raise KeyError(f"Intersection {intersection_id} not found")

        dataset_row = self._latest_rows.get(intersection_id)
        if models_loaded() and not ml_fallback_active():
            return self._predict_with_lstm(
                intersection_id,
                horizon,
                live_state,
                dataset_row,
            )

        return self._predict_with_fallback(
            intersection_id,
            horizon,
            live_state,
            dataset_row,
        )

    def refresh_all_predictions(self) -> None:
        """Refresh AI prediction fields for all registered intersections."""
        for intersection_id in state_store.get_intersection_ids():
            predictions: dict[str, float | None] = {}
            for horizon in HORIZONS:
                result = self.predict(intersection_id, horizon)
                predictions[horizon] = float(result.predicted_vehicle_count)

            state_store.update_state(
                intersection_id,
                {"ai_predictions": predictions},
            )

    def _predict_with_lstm(
        self,
        intersection_id: str,
        horizon: str,
        live_state: LiveIntersectionState,
        dataset_row: DatasetRow | None,
    ) -> PredictionResult:
        """Run Keras inference when artifacts are loaded.

        Args:
            intersection_id: Target intersection identifier.
            horizon: Prediction horizon.
            live_state: Current live intersection state.
            dataset_row: Optional latest dataset row.

        Returns:
            LSTM-backed prediction result.
        """
        features = preprocess.build_feature_vector(
            live_state,
            dataset_row=dataset_row,
        )
        matrix = preprocess.features_to_matrix(features)
        scalers = get_scalers()
        feat_scaler = scalers["feat"]
        target_scaler = self._target_scaler_for_horizon(
            scalers["target"],
            horizon,
        )
        scaled = feat_scaler.transform(matrix)

        config = registry.get_config()
        sequence_length = int(config.get("seq_len", 60))
        if scaled.shape[0] < sequence_length:
            padded = scaled.repeat(sequence_length, axis=0)
        else:
            padded = scaled[-sequence_length:]

        model_input = padded.reshape(1, padded.shape[0], padded.shape[1])
        model = get_model(horizon)
        raw_prediction = model.predict(model_input, verbose=0)
        inverse = target_scaler.inverse_transform(raw_prediction)
        predicted_count = int(max(0, round(float(inverse.ravel()[0]))))

        return PredictionResult(
            intersection_id=intersection_id,
            horizon=horizon,
            predicted_vehicle_count=predicted_count,
            predicted_congestion_level=self._congestion_level(live_state),
            confidence_score=0.9,
            prediction_timestamp=datetime.now(timezone.utc).isoformat(),
            source="lstm",
        )

    def _predict_with_fallback(
        self,
        intersection_id: str,
        horizon: str,
        live_state: LiveIntersectionState,
        dataset_row: DatasetRow | None,
    ) -> PredictionResult:
        """Predict using dataset targets or traffic heuristics.

        Args:
            intersection_id: Target intersection identifier.
            horizon: Prediction horizon.
            live_state: Current live intersection state.
            dataset_row: Optional latest dataset row.

        Returns:
            Fallback prediction result.
        """
        target_volume = preprocess.extract_target_volume(dataset_row, horizon)
        if target_volume is not None:
            predicted_count = int(max(0, round(target_volume)))
            source: Literal["dataset", "heuristic"] = "dataset"
        else:
            base = float(live_state["vehicle_count"])
            predicted_count = int(
                max(0, round(base * HORIZON_VOLUME_SCALE[horizon])),
            )
            source = "heuristic"

        return PredictionResult(
            intersection_id=intersection_id,
            horizon=horizon,
            predicted_vehicle_count=predicted_count,
            predicted_congestion_level=self._congestion_level(live_state),
            confidence_score=0.72 if source == "dataset" else 0.55,
            prediction_timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
        )

    def _congestion_level(
        self,
        live_state: LiveIntersectionState,
    ) -> CongestionLevel:
        """Map occupancy to a congestion label.

        Args:
            live_state: Current live intersection state.

        Returns:
            Congestion level label.
        """
        occupancy = float(live_state["occupancy_rate"])
        if occupancy >= 0.9:
            return "Critical"
        if occupancy >= 0.75:
            return "High"
        if occupancy >= 0.55:
            return "Medium"
        return "Low"

    def _target_scaler_for_horizon(
        self,
        target_scalers: object,
        horizon: str,
    ) -> object:
        """Return the target scaler matching a prediction horizon.

        Args:
            target_scalers: Loaded target scaler artifact.
            horizon: Prediction horizon.

        Returns:
            Scaler object with ``inverse_transform``.

        Raises:
            KeyError: If a scaler dictionary does not contain the horizon.
        """
        if isinstance(target_scalers, dict):
            scaler = target_scalers.get(horizon)
            if scaler is None:
                raise KeyError(f"Target scaler for horizon {horizon} not found")
            return scaler
        return target_scalers


prediction_service = PredictionService()
