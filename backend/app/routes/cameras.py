"""Camera and YOLO readiness routes."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.services.camera_service import camera_service
from core.responses import success_response
from core.schemas import StandardSuccessResponse

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras / YOLO"],
)


@router.get(
    "/status",
    response_model=StandardSuccessResponse,
    summary="Camera and YOLO Status",
    description="Returns readiness metadata for camera input and YOLO integration.",
)
async def camera_status(request: Request) -> StandardSuccessResponse:
    """Return camera and YOLO status.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Standardized camera status response.
    """
    return success_response(
        message="Camera and YOLO status retrieved",
        data=camera_service.status(),
        request_id=request.state.request_id,
    )


@router.get(
    "",
    response_model=StandardSuccessResponse,
    summary="List Camera Slots",
    description="Returns camera slots mapped to simulated intersections.",
)
async def list_cameras(request: Request) -> StandardSuccessResponse:
    """Return configured camera slots.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Standardized camera list response.
    """
    cameras = camera_service.list_cameras()
    return success_response(
        message="Camera slots retrieved",
        data={"count": len(cameras), "cameras": cameras},
        request_id=request.state.request_id,
    )


@router.get(
    "/videos/{period}/{filename}",
    summary="Get Camera Video",
    description="Serves a recorded CCTV video from backend-managed storage.",
)
async def get_camera_video(period: str, filename: str) -> FileResponse:
    """Return a recorded CCTV video file when available."""
    video_path = camera_service.resolve_video_path(period, filename)
    if video_path is None:
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename,
    )
