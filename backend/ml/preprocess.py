"""Feature preparation for Traffix LSTM inference and fallback prediction."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.state_store import LiveIntersectionState
from core.config import settings
from core.paths import resolve_asset_path
from sim.dataset_models import DatasetRow

_FEATURE_COLUMNS_CACHE: list[str] | None = None

HORIZON_TARGET_FIELDS = {
    "15m": "target_volume_15m",
    "2h": "target_volume_2h",
    "4h": "target_volume_4h",
}


def load_feature_columns() -> list[str]:
    """Load and cache Data team feature column names.

    Returns:
        Ordered feature column names from feature_columns.json.
    """
    global _FEATURE_COLUMNS_CACHE
    if _FEATURE_COLUMNS_CACHE is not None:
        return _FEATURE_COLUMNS_CACHE

    path = resolve_asset_path(settings.feature_columns_path)
    if not path.exists():
        _FEATURE_COLUMNS_CACHE = []
        return _FEATURE_COLUMNS_CACHE

    with path.open("r", encoding="utf-8") as feature_file:
        payload = json.load(feature_file)

    if isinstance(payload, list):
        _FEATURE_COLUMNS_CACHE = [str(item) for item in payload]
    else:
        _FEATURE_COLUMNS_CACHE = []

    return _FEATURE_COLUMNS_CACHE


def _weather_one_hot(condition: str) -> dict[str, float]:
    """Build weather one-hot flags from a condition label.

    Args:
        condition: Weather label from live state or dataset.

    Returns:
        Mapping of one-hot weather feature names to values.
    """
    normalized = condition.strip().lower()
    mapping = {
        "clear": "weather_condition_Clear",
        "sunny": "weather_condition_Clear",
        "hot": "weather_condition_Hot",
        "cloudy": "weather_condition_Cloudy",
        "rain": "weather_condition_Rain",
        "rainy": "weather_condition_Rain",
        "storm": "weather_condition_Rain",
    }
    feature_name = mapping.get(normalized, "weather_condition_Cloudy")
    return {
        "weather_condition_Clear": 1.0 if feature_name.endswith("_Clear") else 0.0,
        "weather_condition_Cloudy": 1.0 if feature_name.endswith("_Cloudy") else 0.0,
        "weather_condition_Hot": 1.0 if feature_name.endswith("_Hot") else 0.0,
        "weather_condition_Rain": 1.0 if feature_name.endswith("_Rain") else 0.0,
    }


def build_feature_vector(
    state: LiveIntersectionState,
    *,
    dataset_row: DatasetRow | None = None,
    observed_at: datetime | None = None,
) -> dict[str, float]:
    """Build a feature dictionary from live state and optional dataset row.

    Args:
        state: Current live intersection state.
        dataset_row: Optional latest dataset row for richer features.
        observed_at: Optional observation timestamp override.

    Returns:
        Feature mapping keyed by Data team feature names.
    """
    timestamp = observed_at or datetime.now(timezone.utc)
    hour = timestamp.hour
    minute = timestamp.minute
    day = timestamp.day
    day_of_week = timestamp.weekday()
    month = timestamp.month

    vehicle_count = float(state["vehicle_count"])
    avg_speed = float(state["avg_speed"])
    occupancy = float(state["occupancy_rate"])
    queue_length = float(state["queue_length"])
    green_seconds = float(state["green_duration_seconds"])
    density_percent = min(100.0, occupancy * 100.0)
    volume_per_hour = vehicle_count * 60.0

    features: dict[str, float] = {
        "vehicle_count_1min": vehicle_count,
        "volume_veh_per_hour": volume_per_hour,
        "avg_speed_kmh": avg_speed,
        "queue_length_veh": queue_length,
        "wait_time_min": max(0.0, queue_length / 8.0),
        "green_seconds": green_seconds,
        "density_percent": density_percent,
        "weather_temp_c": 28.0,
        "accident_count": 0.0,
        "roadwork_flag": 0.0,
        "event_flag": 0.0,
        "hour": float(hour),
        "minute": float(minute),
        "day": float(day),
        "day_of_week": float(day_of_week),
        "month": float(month),
        "is_holiday": 0.0,
        "is_weekend": 1.0 if day_of_week >= 5 else 0.0,
        "hour_sin": math.sin(2.0 * math.pi * hour / 24.0),
        "hour_cos": math.cos(2.0 * math.pi * hour / 24.0),
        "delta_volume": 0.0,
        "lag_1": vehicle_count,
        "lag_5": vehicle_count,
        "lag_15": vehicle_count,
        "lag_30": vehicle_count,
        "lag_60": vehicle_count,
        "lag_speed_15": avg_speed,
        "lag_queue_15": queue_length,
        "roll_mean_15": vehicle_count,
        "roll_std_15": 0.0,
        "roll_min_15": vehicle_count,
        "roll_max_15": vehicle_count,
        "roll_median_15": vehicle_count,
        "roll_mean_60": vehicle_count,
        "roll_std_60": 0.0,
        "roll_min_60": vehicle_count,
        "roll_max_60": vehicle_count,
    }
    features.update(_weather_one_hot(state["weather_condition"]))

    if dataset_row is not None:
        features["weather_temp_c"] = float(dataset_row.temperature_celsius)
        features["delta_volume"] = max(
            0.0,
            float(dataset_row.vehicle_count) - vehicle_count,
        )

    return features


def features_to_matrix(
    features: dict[str, float],
    feature_columns: list[str] | None = None,
) -> np.ndarray:
    """Convert a feature dictionary into a model-ready row matrix.

    Args:
        features: Feature mapping keyed by column name.
        feature_columns: Optional ordered feature names.

    Returns:
        Numpy array with shape ``(1, n_features)``.
    """
    columns = feature_columns or load_feature_columns()
    if not columns:
        columns = sorted(features)
    values = [float(features.get(column, 0.0)) for column in columns]
    return np.asarray([values], dtype=np.float32)


def extract_target_volume(dataset_row: DatasetRow | None, horizon: str) -> float | None:
    """Return a dataset target volume for a horizon when available.

    Args:
        dataset_row: Optional dataset row with target columns.
        horizon: Prediction horizon.

    Returns:
        Target volume or None.
    """
    if dataset_row is None:
        return None
    field_name = HORIZON_TARGET_FIELDS.get(horizon)
    if field_name is None:
        return None
    return getattr(dataset_row, field_name, None)
