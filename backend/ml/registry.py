"""In-memory registry for Traffix ML artifacts."""

from dataclasses import dataclass, field
from threading import Lock
from core.constants import HORIZONS


@dataclass
class ModelRegistry:
    """Thread-safe cache for loaded ML models and scaler artifacts."""

    models: dict[str, object] = field(default_factory=dict)
    scalers: dict[str, object] = field(default_factory=dict)
    config: dict[str, object] = field(default_factory=dict)
    fallback_mode: bool = False
    _lock: Lock = field(default_factory=Lock)

    def set_artifacts(
        self,
        models: dict[str, object],
        scalers: dict[str, object],
        config: dict[str, object],
    ) -> None:
        """Store loaded model and scaler artifacts.

        Args:
            models: Loaded Keras models keyed by horizon.
            scalers: Loaded scaler artifacts keyed by scaler name.
            config: Loaded LSTM training configuration.
        """
        with self._lock:
            self.models = models
            self.scalers = scalers
            self.config = config

    def get_model(self, horizon: str) -> object | None:
        """Return a loaded model for a horizon.

        Args:
            horizon: Prediction horizon.

        Returns:
            Loaded model when present, otherwise None.
        """
        with self._lock:
            return self.models.get(horizon)

    def get_scalers(self) -> dict[str, object]:
        """Return loaded scaler artifacts.

        Returns:
            Copy of scaler registry.
        """
        with self._lock:
            return dict(self.scalers)

    def get_config(self) -> dict[str, object]:
        """Return loaded LSTM configuration artifact.

        Returns:
            Copy of config registry.
        """
        with self._lock:
            return dict(self.config)

    def is_loaded(self) -> bool:
        """Return whether all required ML artifacts are loaded.

        Returns:
            True when every horizon model and scaler artifact is cached.
        """
        with self._lock:
            return (
                all(horizon in self.models for horizon in HORIZONS)
                and "feat" in self.scalers
                and "target" in self.scalers
            )

    def set_fallback_mode(self, enabled: bool) -> None:
        """Mark whether ML predictions should use fallback logic.

        Args:
            enabled: True when Keras artifacts are unavailable.
        """
        with self._lock:
            self.fallback_mode = enabled

    def is_fallback_mode(self) -> bool:
        """Return whether ML fallback mode is active.

        Returns:
            True when predictions should not call Keras models.
        """
        with self._lock:
            return self.fallback_mode

    def set_config_only(self, config: dict[str, object]) -> None:
        """Store LSTM config without loading Keras models.

        Args:
            config: Parsed best_config.json contents.
        """
        with self._lock:
            self.config = config

    def clear(self) -> None:
        """Clear all cached ML artifacts."""
        with self._lock:
            self.models.clear()
            self.scalers.clear()
            self.config.clear()
            self.fallback_mode = False


registry = ModelRegistry()
