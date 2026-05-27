"""Async realtime tick engine for hybrid traffic replay."""

import asyncio
from typing import Literal

from app.state_store import LiveIntersectionUpdate, WeatherCondition, state_store
from core.config import settings
from core.logger import get_logger
from ml.predictor import prediction_service
from sim.clock import get_current_wib_time
from sim.congestion_engine import CongestionEngine
from sim.dataset_models import DatasetRow
from sim.replay_controller import ReplayController

simulation_logger = get_logger("simulation")

SignalState = Literal["RED", "YELLOW", "GREEN"]


class TickEngine:
    """Async 2-second replay engine for live traffic state updates."""

    def __init__(
        self,
        replay_controller: ReplayController | None = None,
        congestion_engine: CongestionEngine | None = None,
        tick_interval_seconds: int | None = None,
    ) -> None:
        """Initialize the tick engine.

        Args:
            replay_controller: Optional replay controller dependency.
            congestion_engine: Optional congestion engine dependency.
            tick_interval_seconds: Optional tick interval override.
        """
        self._replay_controller = replay_controller or ReplayController()
        self._congestion_engine = congestion_engine or CongestionEngine()
        self._tick_interval_seconds = (
            tick_interval_seconds or settings.tick_interval_seconds
        )
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._tick_count = 0

    def is_running(self) -> bool:
        """Return whether the tick loop is currently running.

        Returns:
            True when the background tick task is active.
        """
        return self._running

    @property
    def tick_count(self) -> int:
        """Return the number of ticks processed since start.

        Returns:
            Tick counter value.
        """
        return self._tick_count

    async def start(self) -> None:
        """Start the background replay loop if it is not already running."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        simulation_logger.info("Tick engine started")

    async def stop(self) -> None:
        """Stop the background replay loop gracefully."""
        if not self._running:
            return

        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                simulation_logger.info("Tick engine task cancelled")
            finally:
                self._task = None

        simulation_logger.info("Tick engine stopped")

    async def _run_loop(self) -> None:
        """Run ticks until the engine is stopped."""
        try:
            while self._running:
                await self.tick()
                await asyncio.sleep(self._tick_interval_seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            self._running = False
            simulation_logger.exception("Tick engine stopped after error")

    async def tick(self) -> int:
        """Process one replay tick and update live intersection state.

        Returns:
            Number of intersections updated during this tick.
        """
        batch = self._replay_controller.next_batch()
        self._tick_count += 1

        updated_count = 0
        for row in batch:
            if self._update_state_from_row(row):
                updated_count += 1

        if (
            settings.prediction_auto_refresh
            and updated_count > 0
            and batch
        ):
            prediction_service.note_dataset_batch(batch)
            prediction_service.refresh_all_predictions()

        simulation_logger.info(
            "Tick #%s updated %s intersections at %s",
            self._tick_count,
            updated_count,
            get_current_wib_time(),
        )
        return updated_count

    def _update_state_from_row(self, row: DatasetRow) -> bool:
        """Update the state store from one dataset row.

        Args:
            row: Dataset row to apply to live state.

        Returns:
            True when an intersection was updated, otherwise False.
        """
        intersection_id = self._normalize_intersection_id(row.intersection_id)
        if state_store.get_state(intersection_id) is None:
            simulation_logger.warning(
                "Skipping unknown intersection: %s",
                row.intersection_id,
            )
            return False

        result = self._congestion_engine.apply(row)
        payload: LiveIntersectionUpdate = {
            "vehicle_count": result.vehicle_count,
            "avg_speed": result.avg_speed,
            "occupancy_rate": result.occupancy_rate,
            "queue_length": result.queue_length,
            "signal_state": self._signal_state_from_occupancy(
                result.occupancy_rate,
            ),
            "green_duration_seconds": self._green_duration_from_queue(
                result.queue_length,
            ),
            "weather_condition": self._normalize_weather_condition(
                result.weather_condition,
            ),
        }
        state_store.update_state(
            intersection_id,
            payload,
            last_updated=row.timestamp.isoformat(),
        )
        return True

    def _normalize_intersection_id(self, intersection_id: str) -> str:
        """Normalize dataset intersection IDs to state store IDs.

        Args:
            intersection_id: Raw dataset intersection identifier.

        Returns:
            State store compatible intersection identifier.
        """
        known_ids = set(state_store.get_intersection_ids())
        if intersection_id in known_ids:
            return intersection_id
        if intersection_id.isdigit():
            candidate = f"INT-{int(intersection_id):03d}"
            if candidate in known_ids:
                return candidate
        return intersection_id

    def _normalize_weather_condition(
        self,
        weather_condition: str,
    ) -> WeatherCondition:
        """Normalize dataset weather label to frontend-supported values.

        Args:
            weather_condition: Raw dataset weather label.

        Returns:
            Supported weather condition value.
        """
        normalized = weather_condition.strip().lower()
        mapping: dict[str, WeatherCondition] = {
            "clear": "Sunny",
            "sunny": "Sunny",
            "cloudy": "Cloudy",
            "rain": "Rain",
            "rainy": "Rain",
            "storm": "Storm",
            "hot": "Sunny",
        }
        return mapping.get(normalized, "Cloudy")

    def _signal_state_from_occupancy(self, occupancy_rate: float) -> SignalState:
        """Choose a placeholder signal state from occupancy.

        Args:
            occupancy_rate: Lane occupancy ratio from dataset row.

        Returns:
            Signal state for live dashboard replay.
        """
        if occupancy_rate >= 0.85:
            return "GREEN"
        if occupancy_rate >= 0.70:
            return "YELLOW"
        return "GREEN"

    def _green_duration_from_queue(self, queue_length: int) -> int:
        """Choose placeholder green duration from queue length.

        Args:
            queue_length: Queue length from dataset row.

        Returns:
            Green duration in seconds.
        """
        if queue_length >= 30:
            return 75
        if queue_length >= 15:
            return 60
        return 45


tick_engine = TickEngine()
