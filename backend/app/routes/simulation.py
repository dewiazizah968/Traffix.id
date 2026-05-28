"""Simulation control and status routes for Traffix backend."""

from fastapi import APIRouter, Request

from app.runtime_status import runtime_status
from app.state_store import state_store
from core.responses import success_response
from core.schemas import StandardSuccessResponse
from sim.replay_controller import ReplayController
from sim.tick_engine import tick_engine

router = APIRouter(
    prefix="/simulation",
    tags=["Simulation"],
)


@router.get(
    "/status",
    response_model=StandardSuccessResponse,
    summary="Simulation Status",
    description="Returns dataset, replay cursor, and tick engine status.",
)
async def simulation_status(request: Request) -> StandardSuccessResponse:
    """Return simulation integration status.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Standardized simulation status payload.
    """
    replay = ReplayController()
    snapshot = runtime_status.snapshot()
    return success_response(
        message="Simulation status retrieved",
        data={
            **snapshot,
            "simulation_active": tick_engine.is_running(),
            "tick_count": tick_engine.tick_count,
            "replay_cursor": replay.get_cursor(),
            "live_intersections": len(state_store.get_intersection_ids()),
            "dataset_metadata": {
                "rows": snapshot["dataset_rows"],
                "intersections": snapshot["dataset_intersections"],
                "path": snapshot["dataset_path"],
            }
            if snapshot["dataset_ready"]
            else None,
        },
        request_id=request.state.request_id,
    )


@router.post(
    "/start",
    response_model=StandardSuccessResponse,
    summary="Start Simulation",
    description="Start the background replay tick engine.",
)
async def start_simulation(request: Request) -> StandardSuccessResponse:
    """Start the simulation tick engine.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Standardized start response.
    """
    await tick_engine.start()
    return success_response(
        message="Simulation started",
        data={"simulation_active": tick_engine.is_running()},
        request_id=request.state.request_id,
    )


@router.post(
    "/stop",
    response_model=StandardSuccessResponse,
    summary="Stop Simulation",
    description="Stop the background replay tick engine.",
)
async def stop_simulation(request: Request) -> StandardSuccessResponse:
    """Stop the simulation tick engine.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Standardized stop response.
    """
    await tick_engine.stop()
    return success_response(
        message="Simulation stopped",
        data={"simulation_active": tick_engine.is_running()},
        request_id=request.state.request_id,
    )
