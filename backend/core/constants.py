"""
Traffix system-wide constants.

These values are used across routes, simulation, ML inference,
and recommendation engine. Import from here -- never hardcode.
"""

from typing import Final

# ML prediction horizons supported by the LSTM team's trained models.
HORIZONS: Final[list[str]] = ["15m", "2h", "4h"]

# Mapping from horizon string to sequence length in minutes.
HORIZON_MINUTES: Final[dict[str, int]] = {
    "15m": 15,
    "2h": 120,
    "4h": 240,
}

# Traffic signal phase states.
SIGNAL_STATES: Final[list[str]] = ["RED", "YELLOW", "GREEN"]

# Default number of intersections in simulation.
DEFAULT_INTERSECTION_COUNT: int = 4

# Simulation tick rate.
DEFAULT_TICK_INTERVAL_SECONDS: int = 2

# Camera/YOLO.
MAX_CAMERAS: int = 8
VEHICLE_CLASSES: Final[list[str]] = [
    "motorcycle",
    "car",
    "bus",
    "truck",
    "bicycle",
]

# Traffic congestion thresholds (vehicles per minute).
CONGESTION_THRESHOLDS: Final[dict[str, int]] = {
    "low": 10,
    "medium": 25,
    "high": 40,
    "critical": 60,
}
