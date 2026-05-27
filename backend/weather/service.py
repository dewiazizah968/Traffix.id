"""Local weather context service with BMKG-ready metadata."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.state_store import LiveIntersectionState, state_store
from core.config import settings

TEMPERATURE_BY_CONDITION = {
    "Sunny": 31.0,
    "Cloudy": 29.0,
    "Rain": 26.5,
    "Storm": 25.5,
}

HUMIDITY_BY_CONDITION = {
    "Sunny": 64.0,
    "Cloudy": 72.0,
    "Rain": 86.0,
    "Storm": 92.0,
}


class WeatherService:
    """Provide weather context for traffic decisions."""

    def current(
        self,
        intersection_id: str | None = None,
    ) -> dict[str, object]:
        """Return current weather context.

        Args:
            intersection_id: Optional intersection ID.

        Returns:
            Serializable weather payload.

        Raises:
            KeyError: If the intersection is unknown.
        """
        if intersection_id is not None:
            state = state_store.get_state(intersection_id)
            if state is None:
                raise KeyError(f"Intersection {intersection_id} not found")
            return self._weather_from_state(state)

        states = state_store.get_all_states()
        condition_counts: dict[str, int] = {}
        for state in states:
            condition = state["weather_condition"]
            condition_counts[condition] = condition_counts.get(condition, 0) + 1

        dominant_condition = max(
            condition_counts,
            key=condition_counts.get,
        ) if condition_counts else "Cloudy"
        return {
            "scope": "city",
            "provider": "local-simulation",
            "bmkg_api_url": settings.bmkg_api_url,
            "condition": dominant_condition,
            "temperature_celsius": TEMPERATURE_BY_CONDITION[dominant_condition],
            "humidity_percent": HUMIDITY_BY_CONDITION[dominant_condition],
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "intersections": len(states),
            "distribution": condition_counts,
        }

    def forecast(
        self,
        hours: int = 6,
    ) -> list[dict[str, object]]:
        """Return a lightweight traffic-weather forecast.

        Args:
            hours: Number of hours to forecast.

        Returns:
            Hourly forecast payloads.
        """
        base = self.current()
        condition = str(base["condition"])
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        forecast_rows = []
        for offset in range(1, hours + 1):
            timestamp = now + timedelta(hours=offset)
            forecast_rows.append(
                {
                    "forecast_time": timestamp.isoformat(),
                    "condition": condition,
                    "temperature_celsius": round(
                        float(base["temperature_celsius"]) - min(offset, 3) * 0.2,
                        1,
                    ),
                    "humidity_percent": min(
                        100.0,
                        float(base["humidity_percent"]) + offset * 0.5,
                    ),
                    "source": "local-simulation",
                },
            )
        return forecast_rows

    def _weather_from_state(
        self,
        state: LiveIntersectionState,
    ) -> dict[str, object]:
        """Build weather payload from one live state.

        Args:
            state: Live intersection state.

        Returns:
            Serializable weather payload.
        """
        condition = state["weather_condition"]
        return {
            "scope": "intersection",
            "provider": "local-simulation",
            "bmkg_api_url": settings.bmkg_api_url,
            "intersection_id": state["intersection_id"],
            "intersection_name": state["intersection_name"],
            "condition": condition,
            "temperature_celsius": TEMPERATURE_BY_CONDITION[condition],
            "humidity_percent": HUMIDITY_BY_CONDITION[condition],
            "observed_at": state["last_updated"],
        }


weather_service = WeatherService()
