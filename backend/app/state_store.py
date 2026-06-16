"""Thread-safe live intersection state store for Traffix backend."""

from copy import deepcopy
from datetime import datetime, timezone
from threading import Lock
from typing import Final, Literal, NotRequired, Self, TypedDict, TypeAlias

SignalState: TypeAlias = Literal["RED", "YELLOW", "GREEN"]
WeatherCondition: TypeAlias = Literal["Sunny", "Cloudy", "Rain", "Storm"]
StateValue: TypeAlias = str | int | float

DEFAULT_INTERSECTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("INT-001", "GT MERUYA 2B"),
    ("INT-002", "KM 00+600"),
    ("INT-003", "KM 04+600"),
    ("INT-004", "KM 07+200"),
)

UPDATABLE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "vehicle_count",
        "avg_speed",
        "occupancy_rate",
        "queue_length",
        "signal_state",
        "green_duration_seconds",
        "weather_condition",
        "ai_predictions",
    }
)

DEFAULT_AI_PREDICTIONS: Final[dict[str, float | None]] = {
    "15m": None,
    "2h": None,
    "4h": None,
}


class LiveIntersectionState(TypedDict):
    """Frontend-ready live state for one traffic intersection."""

    intersection_id: str
    intersection_name: str
    vehicle_count: int
    avg_speed: float
    occupancy_rate: float
    queue_length: int
    signal_state: SignalState
    green_duration_seconds: int
    weather_condition: WeatherCondition
    ai_predictions: dict[str, float | None]
    last_updated: str


class LiveIntersectionUpdate(TypedDict, total=False):
    """Partial update payload for one traffic intersection."""

    vehicle_count: NotRequired[int]
    avg_speed: NotRequired[float]
    occupancy_rate: NotRequired[float]
    queue_length: NotRequired[int]
    signal_state: NotRequired[SignalState]
    green_duration_seconds: NotRequired[int]
    weather_condition: NotRequired[WeatherCondition]
    ai_predictions: NotRequired[dict[str, float | None]]


def utc_timestamp() -> str:
    """Return the current UTC timestamp in ISO-8601 format.

    Returns:
        Current UTC timestamp string.
    """
    return datetime.now(timezone.utc).isoformat()


class LiveIntersectionStateStore:
    """Singleton thread-safe in-memory live traffic state manager."""

    _instance: Self | None = None
    _instance_lock = Lock()

    def __new__(cls) -> Self:
        """Create or return the singleton state store instance.

        Returns:
            Singleton state store instance.
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """Initialize the store once with default intersection states."""
        if self._initialized:
            return

        self._lock = Lock()
        self._states: dict[str, LiveIntersectionState] = {}
        self.seed_default_states()
        self._initialized = True

    def _build_default_state(
        self,
        intersection_id: str,
        intersection_name: str,
    ) -> LiveIntersectionState:
        """Build a default frontend-ready intersection state.

        Args:
            intersection_id: Stable intersection identifier.
            intersection_name: Human-readable intersection name.

        Returns:
            Default live intersection state.
        """
        return {
            "intersection_id": intersection_id,
            "intersection_name": intersection_name,
            "vehicle_count": 0,
            "avg_speed": 0.0,
            "occupancy_rate": 0.0,
            "queue_length": 0,
            "signal_state": "GREEN",
            "green_duration_seconds": 45,
            "weather_condition": "Sunny",
            "ai_predictions": dict(DEFAULT_AI_PREDICTIONS),
            "last_updated": utc_timestamp(),
        }

    def seed_default_states(self) -> None:
        """Seed the store with four default Surabaya intersections."""
        with self._lock:
            self._states = {
                intersection_id: self._build_default_state(
                    intersection_id,
                    intersection_name,
                )
                for intersection_id, intersection_name in DEFAULT_INTERSECTIONS
            }

    def reset_states(self) -> None:
        """Reset all live states back to default seeded values."""
        self.seed_default_states()

    def get_all_states(self) -> list[LiveIntersectionState]:
        """Return all live intersection states.

        Returns:
            List of frontend-ready intersection state snapshots.
        """
        with self._lock:
            return [
                deepcopy(self._states[intersection_id])
                for intersection_id in sorted(self._states)
            ]

    def get_state(self, intersection_id: str) -> LiveIntersectionState | None:
        """Return a live intersection state by ID.

        Args:
            intersection_id: Stable intersection identifier.

        Returns:
            Intersection state snapshot when found, otherwise None.
        """
        with self._lock:
            state = self._states.get(intersection_id)
            if state is None:
                return None
            return deepcopy(state)

    def get_intersection_ids(self) -> list[str]:
        """Return registered intersection IDs.

        Returns:
            Sorted list of registered intersection identifiers.
        """
        with self._lock:
            return sorted(self._states)

    def update_state(
        self,
        intersection_id: str,
        payload: LiveIntersectionUpdate,
        last_updated: str | None = None,
    ) -> LiveIntersectionState:
        """Update a live intersection state with a partial payload.

        Args:
            intersection_id: Stable intersection identifier.
            payload: Partial frontend-ready state update.
            last_updated: Optional UTC timestamp override.

        Returns:
            Updated intersection state snapshot.

        Raises:
            KeyError: If the intersection ID is not registered.
            ValueError: If the payload contains immutable or unknown fields.
        """
        invalid_fields = set(payload) - UPDATABLE_FIELDS
        if invalid_fields:
            invalid_list = ", ".join(sorted(invalid_fields))
            raise ValueError(f"Unsupported state fields: {invalid_list}")

        with self._lock:
            current = self._states.get(intersection_id)
            if current is None:
                raise KeyError(f"Intersection {intersection_id} not found")

            merged_predictions = dict(current["ai_predictions"])
            if "ai_predictions" in payload:
                merged_predictions.update(payload["ai_predictions"])

            updated: LiveIntersectionState = {
                **current,
                **payload,
                "intersection_id": current["intersection_id"],
                "intersection_name": current["intersection_name"],
                "ai_predictions": merged_predictions,
                "last_updated": last_updated or utc_timestamp(),
            }
            self._states[intersection_id] = updated
            return deepcopy(updated)


state_store = LiveIntersectionStateStore()

# Compatibility aliases for foundation blocks that imported the earlier name.
RuntimeStateStore = LiveIntersectionStateStore
runtime_state_store = state_store
