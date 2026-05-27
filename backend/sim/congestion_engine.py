"""Congestion escalation engine for realistic traffic replay."""

from dataclasses import dataclass
from random import Random

from sim.dataset_models import DatasetRow
from sim.incidents import IncidentConfig, apply_accident_modifier
from sim.modifiers import (
    TrafficSnapshot,
    apply_queue_buildup_modifier,
    apply_rush_hour_modifier,
    apply_speed_degradation_modifier,
    apply_weather_modifier,
    clamp_snapshot,
)


@dataclass(frozen=True)
class CongestionResult:
    """Output of the congestion escalation engine."""

    vehicle_count: int
    avg_speed: float
    occupancy_rate: float
    queue_length: int
    weather_condition: str
    accident_active: bool


class CongestionEngine:
    """Apply deterministic and probabilistic realism modifiers."""

    def __init__(
        self,
        incident_config: IncidentConfig | None = None,
        rng: Random | None = None,
    ) -> None:
        """Initialize the congestion engine.

        Args:
            incident_config: Optional accident configuration.
            rng: Optional random number generator dependency.
        """
        self._incident_config = incident_config or IncidentConfig()
        self._rng = rng or Random()

    def apply(self, row: DatasetRow) -> CongestionResult:
        """Apply congestion escalation logic to one dataset row.

        Args:
            row: Dataset row from replay loader.

        Returns:
            Realistic congestion result for state store updates.
        """
        snapshot = TrafficSnapshot(
            vehicle_count=row.vehicle_count,
            avg_speed=row.avg_speed,
            occupancy_rate=row.occupancy_rate,
            queue_length=row.queue_length,
            weather_condition=row.weather_condition,
            timestamp=row.timestamp,
        )

        snapshot = apply_rush_hour_modifier(snapshot)
        snapshot = apply_weather_modifier(snapshot)
        snapshot = apply_queue_buildup_modifier(snapshot)
        snapshot = apply_speed_degradation_modifier(snapshot)
        incident = apply_accident_modifier(
            snapshot,
            self._rng,
            self._incident_config,
        )
        snapshot = clamp_snapshot(incident.snapshot)

        return CongestionResult(
            vehicle_count=snapshot.vehicle_count,
            avg_speed=round(snapshot.avg_speed, 2),
            occupancy_rate=round(snapshot.occupancy_rate, 4),
            queue_length=snapshot.queue_length,
            weather_condition=snapshot.weather_condition,
            accident_active=incident.accident_active,
        )
