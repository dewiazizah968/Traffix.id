"""Intersection live-state routes for Traffix backend."""

from fastapi import APIRouter, HTTPException, Request

from app.serializers import serialize_live_intersection
from app.state_store import state_store
from core.responses import success_response
from core.schemas import StandardSuccessResponse

router = APIRouter(
    prefix="/intersections",
    tags=["Intersections"],
)


@router.get(
    "",
    response_model=StandardSuccessResponse,
    summary="List Intersections",
    description="Returns live traffic state for all registered intersections.",
)
async def list_intersections(request: Request) -> StandardSuccessResponse:
    """Return all live intersection states.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Standardized response with intersection list.
    """
    states = state_store.get_all_states()
    return success_response(
        message="Live intersection states retrieved",
        data={
            "count": len(states),
            "intersections": [
                serialize_live_intersection(state) for state in states
            ],
        },
        request_id=request.state.request_id,
    )


@router.get(
    "/{intersection_id}",
    response_model=StandardSuccessResponse,
    summary="Get Intersection",
    description="Returns live traffic state for one intersection.",
)
async def get_intersection(
    intersection_id: str,
    request: Request,
) -> StandardSuccessResponse:
    """Return one live intersection state.

    Args:
        intersection_id: Target intersection identifier.
        request: Incoming FastAPI request.

    Returns:
        Standardized response with one intersection payload.

    Raises:
        HTTPException: When the intersection is not registered.
    """
    state = state_store.get_state(intersection_id.upper())
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"Intersection {intersection_id} not found",
        )

    return success_response(
        message="Live intersection state retrieved",
        data=serialize_live_intersection(state),
        request_id=request.state.request_id,
    )
