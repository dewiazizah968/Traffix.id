"""Application startup integration for dataset, ML, and simulation."""

from __future__ import annotations

import json

from app.runtime_status import runtime_status
from core.config import settings
from core.logger import get_logger
from core.paths import resolve_asset_path
from ml.model_loader import try_load_models
from ml.registry import registry
from sim.dataset_loader import (
    DatasetLoaderError,
    HybridTrafficDatasetLoader,
)
from sim.tick_engine import tick_engine

system_logger = get_logger("system")


def _load_lstm_config_only() -> None:
    """Load LSTM JSON config when Keras artifacts are unavailable."""
    config_path = resolve_asset_path(settings.lstm_config_path)
    if not config_path.exists():
        system_logger.warning("LSTM config not found: %s", config_path)
        return

    with config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    registry.set_config_only(config)
    system_logger.info("Loaded LSTM config from %s", config_path)


async def startup_integrations() -> None:
    """Initialize dataset, ML, and simulation integrations."""
    loader = HybridTrafficDatasetLoader()
    try:
        metadata = loader.get_dataset_metadata()
        runtime_status.update_dataset(
            ready=True,
            rows=metadata.rows,
            intersections=metadata.intersections,
            path=str(loader.dataset_path),
        )
        system_logger.info(
            "Dataset ready: %s rows, %s intersections at %s",
            metadata.rows,
            metadata.intersections,
            loader.dataset_path,
        )
    except DatasetLoaderError as exc:
        runtime_status.update_dataset(ready=False)
        system_logger.error("Dataset integration failed: %s", exc)

    if settings.ml_auto_load:
        if try_load_models():
            runtime_status.set_ml_mode("loaded")
            system_logger.info("ML artifacts loaded successfully")
        elif settings.ml_allow_fallback:
            _load_lstm_config_only()
            registry.set_fallback_mode(True)
            runtime_status.set_ml_mode("fallback")
            system_logger.warning(
                "ML Keras artifacts missing; using dataset/heuristic fallback",
            )
        else:
            runtime_status.set_ml_mode("disabled")
    else:
        runtime_status.set_ml_mode("disabled")

    if settings.simulation_auto_start and runtime_status.dataset_ready:
        await tick_engine.start()
        system_logger.info("Simulation tick engine auto-started")
    elif not runtime_status.dataset_ready:
        system_logger.warning("Simulation not started because dataset is unavailable")


async def shutdown_integrations() -> None:
    """Stop background integrations gracefully."""
    await tick_engine.stop()
