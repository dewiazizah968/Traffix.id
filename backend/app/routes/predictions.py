"""Prediction routes for Traffix multi-horizon LSTM and fallback modes."""

from fastapi import APIRouter, HTTPException, Request

from app.runtime_status import runtime_status
from app.services.inference_insight_service import inference_insight_service
from app.state_store import state_store
from core.constants import HORIZONS
from core.responses import success_response
from core.schemas import PredictionRequest, StandardSuccessResponse
from ml.model_loader import ml_fallback_active, models_loaded
from ml.predictor import prediction_service

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)


def _serialize_prediction(result: object) -> dict[str, object]:
    """Convert a prediction result dataclass to a response dict.

    Args:
        result: PredictionResult instance.

    Returns:
        JSON-serializable prediction payload.
    """
    return {
        "intersection_id": result.intersection_id,
        "horizon": result.horizon,
        "predicted_vehicle_count": result.predicted_vehicle_count,
        "predicted_congestion_level": result.predicted_congestion_level,
        "confidence_score": result.confidence_score,
        "prediction_timestamp": result.prediction_timestamp,
        "source": result.source,
    }


@router.get(
    "/{intersection_id}",
    response_model=StandardSuccessResponse,
    summary="List Predictions",
    description="Returns cached and on-demand predictions for all horizons.",
)
async def list_predictions(
    intersection_id: str,
    request: Request,
) -> StandardSuccessResponse:
    """Return predictions for all supported horizons.

    Args:
        intersection_id: Target intersection identifier.
        request: Incoming FastAPI request.

    Returns:
        Standardized response with per-horizon predictions.

    Raises:
        HTTPException: When the intersection is not registered.
    """
    normalized_id = intersection_id.upper()
    if state_store.get_state(normalized_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Intersection {intersection_id} not found",
        )

    predictions = [
        _serialize_prediction(
            prediction_service.predict(normalized_id, horizon),
        )
        for horizon in HORIZONS
    ]
    insight = inference_insight_service.get_insight(normalized_id)

    return success_response(
        message="Predictions generated",
        data={
            "intersection_id": normalized_id,
            "ml_models_loaded": models_loaded(),
            "ml_fallback_active": ml_fallback_active(),
            "ml_mode": runtime_status.snapshot()["ml_mode"],
            "predictions": predictions,
            "ai_insight": insight.get("ai_insight") if insight else None,
            "recommendation": insight.get("recommendation") if insight else None,
            "recommended_green_seconds": (
                insight.get("recommended_green_seconds") if insight else None
            ),
            "congestion_level": insight.get("congestion_level") if insight else None,
            "inference_source": insight.get("source") if insight else None,
        },
        request_id=request.state.request_id,
    )


@router.post(
    "",
    response_model=StandardSuccessResponse,
    summary="Predict Horizon",
    description="Generate a prediction for one intersection and horizon.",
)
async def predict_horizon(
    payload: PredictionRequest,
    request: Request,
) -> StandardSuccessResponse:
    """Generate a single-horizon prediction.

    Args:
        payload: Prediction request body.
        request: Incoming FastAPI request.

    Returns:
        Standardized response with one prediction.

    Raises:
        HTTPException: When the intersection is not registered.
    """
    normalized_id = payload.intersection_id.upper()
    if state_store.get_state(normalized_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Intersection {payload.intersection_id} not found",
        )

    result = prediction_service.predict(normalized_id, payload.horizon)
    return success_response(
        message="Prediction generated",
        data=_serialize_prediction(result),
        request_id=request.state.request_id,
    )
