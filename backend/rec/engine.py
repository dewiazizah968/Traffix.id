"""Rule-based signal recommendation service."""

from dataclasses import dataclass
from typing import Literal

from app.state_store import LiveIntersectionState, state_store
from core.constants import HORIZONS

RecommendationPriority = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass(frozen=True)
class SignalRecommendation:
    """Signal timing recommendation for one intersection."""

    intersection_id: str
    current_green_seconds: int
    recommended_green_seconds: int
    delta_seconds: int
    reason: str
    congestion_risk_percent: float
    priority: RecommendationPriority


class RecommendationService:
    """Generate rule-based traffic signal recommendations."""

    def recommend(self, intersection_id: str) -> SignalRecommendation:
        """Recommend a green-light duration for an intersection.

        Args:
            intersection_id: Target live-state intersection ID.

        Returns:
            Signal timing recommendation.

        Raises:
            KeyError: If the intersection is unknown.
        """
        state = state_store.get_state(intersection_id)
        if state is None:
            raise KeyError(f"Intersection {intersection_id} not found")
        return self._recommend_from_state(state)

    def recommend_all(self) -> list[SignalRecommendation]:
        """Return recommendations for every registered intersection.

        Returns:
            List of recommendations sorted by risk descending.
        """
        recommendations = [
            self._recommend_from_state(state)
            for state in state_store.get_all_states()
        ]
        return sorted(
            recommendations,
            key=lambda item: item.congestion_risk_percent,
            reverse=True,
        )

    def _recommend_from_state(
        self,
        state: LiveIntersectionState,
    ) -> SignalRecommendation:
        """Build a recommendation from one live state snapshot.

        Args:
            state: Live intersection state.

        Returns:
            Recommendation object.
        """
        risk = self._risk_percent(state)
        current_green = int(state["green_duration_seconds"])
        recommended_green = self._recommended_green_seconds(risk, state)
        reason = self._reason(risk, state)
        return SignalRecommendation(
            intersection_id=state["intersection_id"],
            current_green_seconds=current_green,
            recommended_green_seconds=recommended_green,
            delta_seconds=recommended_green - current_green,
            reason=reason,
            congestion_risk_percent=round(risk, 2),
            priority=self._priority(risk),
        )

    def _risk_percent(self, state: LiveIntersectionState) -> float:
        """Estimate congestion risk from live metrics and predictions.

        Args:
            state: Live intersection state.

        Returns:
            Risk percentage in [0, 100].
        """
        occupancy_risk = float(state["occupancy_rate"]) * 100.0
        queue_risk = min(100.0, float(state["queue_length"]) * 3.0)
        speed_risk = max(0.0, 100.0 - float(state["avg_speed"]) * 2.0)
        prediction_values = [
            value
            for horizon in HORIZONS
            if (value := state["ai_predictions"].get(horizon)) is not None
        ]
        prediction_risk = (
            min(100.0, max(prediction_values) / 25.0)
            if prediction_values
            else occupancy_risk
        )
        risk = (
            occupancy_risk * 0.35
            + queue_risk * 0.25
            + speed_risk * 0.15
            + prediction_risk * 0.25
        )
        return max(0.0, min(100.0, risk))

    def _recommended_green_seconds(
        self,
        risk: float,
        state: LiveIntersectionState,
    ) -> int:
        """Choose a green-light duration from risk and queue length.

        Args:
            risk: Congestion risk percentage.
            state: Live intersection state.

        Returns:
            Recommended duration in seconds.
        """
        queue_length = int(state["queue_length"])
        if risk >= 85.0 or queue_length >= 30:
            return 90
        if risk >= 70.0 or queue_length >= 20:
            return 75
        if risk >= 50.0 or queue_length >= 12:
            return 60
        return 45

    def _reason(self, risk: float, state: LiveIntersectionState) -> str:
        """Explain why a recommendation was generated.

        Args:
            risk: Congestion risk percentage.
            state: Live intersection state.

        Returns:
            Human-readable reason.
        """
        if risk >= 85.0:
            return "Critical congestion risk from predicted demand and queue length."
        if risk >= 70.0:
            return "High congestion risk; extend green duration to drain queues."
        if risk >= 50.0:
            return "Moderate congestion risk; keep a longer green phase available."
        return "Traffic is stable; keep default green duration."

    def _priority(self, risk: float) -> RecommendationPriority:
        """Map risk percentage to priority label.

        Args:
            risk: Congestion risk percentage.

        Returns:
            Priority label.
        """
        if risk >= 85.0:
            return "CRITICAL"
        if risk >= 70.0:
            return "HIGH"
        if risk >= 50.0:
            return "MEDIUM"
        return "LOW"


recommendation_service = RecommendationService()
