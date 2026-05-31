"""Incident simulation helpers for traffic replay realism."""

from dataclasses import dataclass, replace
from random import Random

from sim.modifiers import TrafficSnapshot, clamp_float, clamp_int


@dataclass(frozen=True)
class IncidentConfig:
    """Configuration for accident probability and impact."""

    accident_probability: float = 0.03
    min_probability: float = 0.02
    max_probability: float = 0.05
    queue_multiplier: float = 1.45
    speed_multiplier: float = 0.55
    occupancy_multiplier: float = 1.20


@dataclass(frozen=True)
class IncidentResult:
    """Result of applying incident logic to a traffic snapshot."""

    snapshot: TrafficSnapshot
    accident_active: bool


def normalized_accident_probability(config: IncidentConfig) -> float:
    """Return accident probability clamped to realistic bounds.

    Args:
        config: Incident configuration.

    Returns:
        Probability between configured min and max values.
    """
    return clamp_float(
        config.accident_probability,
        config.min_probability,
        config.max_probability,
    )


def should_trigger_accident(
    rng: Random,
    config: IncidentConfig,
) -> bool:
    """Return whether an accident should trigger for a tick.

    Args:
        rng: Random number generator dependency.
        config: Incident configuration.

    Returns:
        True when the accident threshold is met.
    """
    return rng.random() < normalized_accident_probability(config)


def apply_accident_modifier(
    snapshot: TrafficSnapshot,
    rng: Random,
    config: IncidentConfig | None = None,
) -> IncidentResult:
    """Apply occasional accident impact to traffic values.

    Args:
        snapshot: Input traffic snapshot.
        rng: Random number generator dependency.
        config: Optional incident configuration.

    Returns:
        Incident result with modified snapshot and active flag.
    """
    active_config = config or IncidentConfig()
    if not should_trigger_accident(rng, active_config):
        return IncidentResult(snapshot=snapshot, accident_active=False)

    modified = replace(
        snapshot,
        queue_length=clamp_int(
            round(snapshot.queue_length * active_config.queue_multiplier) + 8,
            0,
            250,
        ),
        avg_speed=clamp_float(
            snapshot.avg_speed * active_config.speed_multiplier,
            1.0,
            120.0,
        ),
        occupancy_rate=clamp_float(
            snapshot.occupancy_rate * active_config.occupancy_multiplier,
            0.0,
            1.0,
        ),
    )
    return IncidentResult(snapshot=modified, accident_active=True)
