"""Shared runtime integration flags for Traffix backend."""

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RuntimeStatus:
    """Mutable runtime status used by system and simulation endpoints."""

    dataset_ready: bool = False
    dataset_rows: int = 0
    dataset_intersections: int = 0
    dataset_path: str | None = None
    ml_mode: str = "uninitialized"
    simulation_ready: bool = False
    _lock: Lock = field(default_factory=Lock)

    def update_dataset(
        self,
        *,
        ready: bool,
        rows: int = 0,
        intersections: int = 0,
        path: str | None = None,
    ) -> None:
        """Update dataset readiness metadata.

        Args:
            ready: Whether the hybrid dataset loaded successfully.
            rows: Number of dataset rows.
            intersections: Unique intersection count.
            path: Resolved dataset path.
        """
        with self._lock:
            self.dataset_ready = ready
            self.dataset_rows = rows
            self.dataset_intersections = intersections
            self.dataset_path = path
            self.simulation_ready = ready

    def set_ml_mode(self, mode: str) -> None:
        """Update ML integration mode label.

        Args:
            mode: One of loaded, fallback, disabled, or error.
        """
        with self._lock:
            self.ml_mode = mode

    def snapshot(self) -> dict[str, object]:
        """Return a thread-safe status snapshot.

        Returns:
            Serializable runtime status mapping.
        """
        with self._lock:
            return {
                "dataset_ready": self.dataset_ready,
                "dataset_rows": self.dataset_rows,
                "dataset_intersections": self.dataset_intersections,
                "dataset_path": self.dataset_path,
                "ml_mode": self.ml_mode,
                "simulation_ready": self.simulation_ready,
            }


runtime_status = RuntimeStatus()
