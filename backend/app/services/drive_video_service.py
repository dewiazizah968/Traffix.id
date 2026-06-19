"""Google Drive integration for on-demand CCTV video caching.

Videos are stored in a Google Drive folder structured as:
    <root_folder>/pagi/*.mp4
    <root_folder>/siang/*.mp4
    <root_folder>/malam/*.mp4

This service authenticates with a service account, resolves period
subfolders, and downloads a requested file into local backend storage
the first time it is requested. Subsequent requests are served from
the local cache (see ``camera_service.resolve_video_path``).
"""

from __future__ import annotations

import io
import json
import logging
import threading
from pathlib import Path

from core.config import settings
from core.paths import resolve_asset_path

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Guards concurrent downloads of the same file across requests.
_download_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()

# Cache of resolved period-subfolder Drive IDs to avoid repeat list calls.
_period_folder_cache: dict[str, str] = {}


class DriveVideoServiceError(RuntimeError):
    """Raised when Drive video retrieval fails for a reason worth logging."""


def _get_lock(key: str) -> threading.Lock:
    """Return a per-file lock so concurrent requests don't double-download."""
    with _locks_guard:
        if key not in _download_locks:
            _download_locks[key] = threading.Lock()
        return _download_locks[key]


def is_configured() -> bool:
    """Return whether Drive video caching has the settings it needs."""
    return bool(
        settings.google_service_account_json
        and settings.camera_video_drive_folder_id,
    )


def _build_drive_client():
    """Build an authenticated Drive API client from the service account.

    Returns:
        A ``googleapiclient.discovery.Resource`` for the Drive v3 API.

    Raises:
        DriveVideoServiceError: If credentials are missing or invalid, or
            the optional Google API client libraries are not installed.
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - depends on optional deps
        raise DriveVideoServiceError(
            "google-api-python-client / google-auth is not installed",
        ) from exc

    raw = settings.google_service_account_json
    if not raw:
        raise DriveVideoServiceError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")

    try:
        info = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise DriveVideoServiceError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON",
        ) from exc

    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=_SCOPES,
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def _find_period_folder_id(period: str) -> str | None:
    """Resolve and cache the Drive folder id for a CCTV period (pagi/siang/malam)."""
    if period in _period_folder_cache:
        return _period_folder_cache[period]

    drive = _build_drive_client()
    root_id = settings.camera_video_drive_folder_id
    query = (
        f"'{root_id}' in parents and name = '{period}' "
        "and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    response = (
        drive.files()
        .list(q=query, fields="files(id, name)", pageSize=5)
        .execute()
    )
    files = response.get("files", [])
    if not files:
        return None

    folder_id = files[0]["id"]
    _period_folder_cache[period] = folder_id
    return folder_id


def _find_file_id(period: str, filename: str) -> str | None:
    """Find the Drive file id for a video filename within a period folder."""
    folder_id = _find_period_folder_id(period)
    if folder_id is None:
        return None

    drive = _build_drive_client()
    safe_name = filename.replace("'", "\\'")
    query = f"'{folder_id}' in parents and name = '{safe_name}' and trashed = false"
    response = (
        drive.files()
        .list(q=query, fields="files(id, name)", pageSize=5)
        .execute()
    )
    files = response.get("files", [])
    if not files:
        return None
    return files[0]["id"]


def ensure_video_cached(period: str, filename: str) -> Path | None:
    """Ensure a CCTV video is present in local cache, downloading it if needed.

    Args:
        period: CCTV period folder name (e.g. "pagi", "siang", "malam").
        filename: Video filename, e.g. "CAM-001_07-15.mp4".

    Returns:
        Local path to the cached video, or None if it could not be
        located/downloaded (caller should treat this as "not found").
    """
    if not is_configured():
        return None

    video_root = resolve_asset_path(settings.camera_video_root_path)
    target_dir = video_root / period
    target_path = target_dir / filename

    if target_path.exists() and target_path.stat().st_size > 0:
        return target_path

    lock_key = f"{period}/{filename}"
    lock = _get_lock(lock_key)
    with lock:
        # Re-check after acquiring the lock in case another request
        # already finished downloading this file.
        if target_path.exists() and target_path.stat().st_size > 0:
            return target_path

        try:
            from googleapiclient.http import MediaIoBaseDownload

            file_id = _find_file_id(period, filename)
            if file_id is None:
                logger.warning(
                    "Video not found on Drive: period=%s filename=%s",
                    period,
                    filename,
                )
                return None

            drive = _build_drive_client()
            request = drive.files().get_media(fileId=file_id)

            target_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = target_path.with_suffix(target_path.suffix + ".part")

            with tmp_path.open("wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _status, done = downloader.next_chunk()

            tmp_path.rename(target_path)
            logger.info("Cached video from Drive: %s", target_path)
            return target_path
        except DriveVideoServiceError as exc:
            logger.error("Drive video service misconfigured: %s", exc)
            return None
        except Exception:  # noqa: BLE001 - external API call, log and degrade
            logger.exception(
                "Failed to download video from Drive: period=%s filename=%s",
                period,
                filename,
            )
            return None
