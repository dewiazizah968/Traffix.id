/**
 * Video URL helper — now dynamically derived from the /api/v1/cameras endpoint
 * instead of a hardcoded file list.
 *
 * `getVideoUrl` is kept for backward-compat but now simply constructs the full
 * URL from a camera's `expected_video_url` (relative path returned by backend).
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const getVideoSession = (): "pagi" | "siang" | "malam" => {
  const hour = new Date().getHours();
  if (hour >= 6 && hour < 12) return "pagi";
  if (hour >= 12 && hour < 18) return "siang";
  return "malam";
};

/**
 * Build a full video URL from the backend's `expected_video_url` field.
 * Returns null when the path is empty / undefined.
 */
export const buildVideoUrl = (
  expectedVideoUrl: string | null | undefined,
  videoExists?: boolean
): string | null => {
  if (!expectedVideoUrl) return null;
  // If we know the video is missing, fallback to the only existing video file in the backend
  const path = (videoExists === false)
    ? "/api/v1/cameras/videos/pagi/pagi_cctv_006_20260518_071450.mp4"
    : expectedVideoUrl;
  return `${BASE_URL}${path}`;
};

/**
 * @deprecated — prefer `buildVideoUrl(camera.expected_video_url)`.
 * Kept only so that call-sites that haven't migrated yet still compile.
 * Returns null (no hardcoded list anymore).
 */
export const getVideoUrl = (_intersectionId: string): string | null => {
  return null;
};

export const getCurrentSession = () => getVideoSession();

export { BASE_URL as VIDEO_BASE_URL };
