"""Lazy multi-horizon LSTM model loader for Traffix predictions."""

import json
from pathlib import Path

from core.config import settings
from core.constants import HORIZONS
from core.logger import get_logger
from core.paths import resolve_asset_path
from ml.registry import registry

ml_logger = get_logger("ml")


class MLArtifactError(Exception):
    """Base exception for ML artifact loading failures."""


class MLArtifactNotFoundError(MLArtifactError):
    """Raised when one or more configured ML artifacts are missing."""


class UnsupportedHorizonError(MLArtifactError):
    """Raised when a requested prediction horizon is unsupported."""


def _resolve_path(path_value: str) -> Path:
    """Resolve an artifact path relative to backend or repo root.

    Args:
        path_value: Configured artifact path.

    Returns:
        Absolute artifact path.
    """
    return resolve_asset_path(path_value)


def _artifact_paths() -> dict[str, Path]:
    """Return required ML artifact paths from settings.

    Returns:
        Mapping of artifact keys to resolved paths.
    """
    lstm_paths = settings.get_lstm_paths()
    return {
        "lstm_15m": _resolve_path(lstm_paths["15m"]),
        "lstm_2h": _resolve_path(lstm_paths["2h"]),
        "lstm_4h": _resolve_path(lstm_paths["4h"]),
        "feat_scaler": _resolve_path(settings.feat_scaler_path),
        "target_scaler": _resolve_path(settings.target_scaler_path),
        "lstm_config": _resolve_path(settings.lstm_config_path),
    }


def validate_artifacts() -> dict[str, Path]:
    """Validate all configured ML artifact files exist.

    Returns:
        Mapping of artifact keys to resolved paths.

    Raises:
        MLArtifactNotFoundError: If any required artifact is missing.
    """
    paths = _artifact_paths()
    missing = [f"{key}={path}" for key, path in paths.items() if not path.exists()]
    if missing:
        missing_text = "; ".join(missing)
        raise MLArtifactNotFoundError(f"Missing ML artifacts: {missing_text}")
    return paths


def load_models() -> None:
    """Lazy-load and cache all multi-horizon LSTM artifacts.

    Raises:
        MLArtifactNotFoundError: If configured artifacts are missing.
        MLArtifactError: If TensorFlow/joblib loading fails.
    """
    if registry.is_loaded():
        ml_logger.info("ML artifacts already loaded; using cache")
        return

    paths = validate_artifacts()
    ml_logger.info("Loading Traffix LSTM artifacts")

    try:
        import joblib
        from tensorflow.keras.models import load_model
    except ImportError as exc:
        raise MLArtifactError(
            "TensorFlow and joblib are required for Keras inference. "
            "Install backend requirements: pip install -r requirements.txt",
        ) from exc

    try:
        models = {
            "15m": load_model(paths["lstm_15m"], compile=False),
            "2h": load_model(paths["lstm_2h"], compile=False),
            "4h": load_model(paths["lstm_4h"], compile=False),
        }
        scalers = {
            "feat": joblib.load(paths["feat_scaler"]),
            "target": joblib.load(paths["target_scaler"]),
        }
        with paths["lstm_config"].open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except Exception as exc:
        raise MLArtifactError("Failed to load ML artifacts") from exc

    registry.set_artifacts(models=models, scalers=scalers, config=config)
    ml_logger.info("Loaded LSTM models for horizons: %s", HORIZONS)


def get_model(horizon: str) -> object:
    """Return the loaded Keras model for a prediction horizon.

    Args:
        horizon: Prediction horizon, one of 15m, 2h, or 4h.

    Returns:
        Loaded Keras model object.

    Raises:
        UnsupportedHorizonError: If the horizon is not supported.
    """
    if horizon not in HORIZONS:
        raise UnsupportedHorizonError(f"Unsupported horizon: {horizon}")
    if not registry.is_loaded():
        load_models()

    model = registry.get_model(horizon)
    if model is None:
        raise MLArtifactError(f"Model for horizon {horizon} is not loaded")
    return model


def get_scalers() -> dict[str, object]:
    """Return loaded feature and target scalers.

    Returns:
        Mapping with `feat` and `target` scaler artifacts.
    """
    if not registry.is_loaded():
        load_models()
    return registry.get_scalers()


def get_model_config() -> dict[str, object]:
    """Return loaded LSTM configuration.

    Returns:
        Loaded model configuration from best_config.json.
    """
    if not registry.is_loaded():
        load_models()
    return registry.get_config()


def try_load_models() -> bool:
    """Attempt to load ML artifacts without raising to callers.

    Returns:
        True when all configured artifacts were loaded successfully.
    """
    try:
        load_models()
        registry.set_fallback_mode(False)
        return True
    except MLArtifactNotFoundError as exc:
        ml_logger.warning("ML artifact files missing: %s", exc)
        registry.set_fallback_mode(True)
        return False
    except MLArtifactError as exc:
        ml_logger.warning("ML load failed: %s", exc)
        registry.set_fallback_mode(True)
        return False


def models_loaded() -> bool:
    """Return whether all required ML artifacts are loaded.

    Returns:
        True when models and scalers are cached.
    """
    return registry.is_loaded()


def ml_fallback_active() -> bool:
    """Return whether the backend is using non-Keras prediction fallback.

    Returns:
        True when fallback mode is enabled.
    """
    return registry.is_fallback_mode()


def is_models_loaded() -> bool:
    """Backward-compatible alias for `models_loaded`.

    Returns:
        True when models and scalers are cached.
    """
    return models_loaded()
