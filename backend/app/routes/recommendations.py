"""Recommendation routes for adaptive signal timing."""

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request

from core.responses import success_response
from core.schemas import StandardSuccessResponse
from rec.engine import recommendation_service

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get(
    "",
    response_model=StandardSuccessResponse,
    summary="List Signal Recommendations",
    description="Returns rule-based signal timing recommendations for all intersections.",
)
async def list_recommendations(request: Request) -> StandardSuccessResponse:
    """Return recommendations for all intersections.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Standardized response with sorted recommendation list.
    """
    recommendations = recommendation_service.recommend_all()
    return success_response(
        message="Signal recommendations generated",
        data={
            "count": len(recommendations),
            "recommendations": [asdict(item) for item in recommendations],
        },
        request_id=request.state.request_id,
    )


@router.get(
    "/{intersection_id}",
    response_model=StandardSuccessResponse,
    summary="Get Signal Recommendation",
    description="Returns a signal timing recommendation for one intersection.",
)
async def get_recommendation(
    intersection_id: str,
    request: Request,
) -> StandardSuccessResponse:
    """Return one intersection recommendation.

    Args:
        intersection_id: Target intersection identifier.
        request: Incoming FastAPI request.

    Returns:
        Standardized response with one recommendation.

    Raises:
        HTTPException: When the intersection is unknown.
    """
    normalized_id = intersection_id.upper()
    try:
        recommendation = recommendation_service.recommend(normalized_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return success_response(
        message="Signal recommendation generated",
        data=asdict(recommendation),
        request_id=request.state.request_id,
    )
