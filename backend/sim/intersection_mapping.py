"""Dataset intersection ID mapping for Traffix live state store."""

from typing import Final

# Data team synthetic IDs mapped to Jakarta-Tangerang dashboard intersections.
DATASET_TO_STORE: Final[dict[str, str]] = {
    "JKT-TMG-SIM-01": "INT-001",
    "1": "INT-001",
    "2": "INT-002",
    "3": "INT-003",
    "4": "INT-004",
}

# When the CSV only contains one physical intersection, fan out to dashboard IDs.
DEMO_INTERSECTION_SCALE: Final[dict[str, float]] = {
    "INT-001": 1.0,
    "INT-002": 0.88,
    "INT-003": 1.12,
    "INT-004": 0.95,
}

DEMO_INTERSECTION_IDS: Final[tuple[str, ...]] = tuple(DEMO_INTERSECTION_SCALE)


def map_dataset_intersection_id(raw_id: str) -> str:
    """Map a dataset intersection identifier to a state store ID.

    Args:
        raw_id: Intersection identifier from the hybrid traffic CSV.

    Returns:
        Mapped state store intersection identifier.
    """
    normalized = raw_id.strip()
    if normalized in DATASET_TO_STORE:
        return DATASET_TO_STORE[normalized]
    if normalized.isdigit():
        candidate = f"INT-{int(normalized):03d}"
        if candidate in DEMO_INTERSECTION_SCALE:
            return candidate
    return normalized
