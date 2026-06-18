import { useState, useEffect, useRef } from "react";
import {
  useWeatherByIntersection,
  useCameraByIntersection,
} from "../../hooks/useTraffixData";
import { buildVideoUrl } from "../../lib/videoMap";
import type { Intersection } from "../../types";

const badge = (rate: number) => {
  if (rate >= 0.75)
    return {
      color: "var(--red)",
      bg: "var(--red-bg)",
      border: "var(--red-border)",
      label: "HEAVY",
    };
  if (rate >= 0.45)
    return {
      color: "var(--yellow)",
      bg: "var(--yellow-bg)",
      border: "var(--yellow-border)",
      label: "MOD",
    };
  return {
    color: "var(--green)",
    bg: "var(--green-bg)",
    border: "var(--green-border)",
    label: "OK",
  };
};

const congestionBadge = (level: string) => {
  const map: Record<string, { color: string; bg: string; border: string; label: string }> = {
    Low: { color: "var(--green)", bg: "var(--green-bg)", border: "var(--green-border)", label: "Rendah" },
    Medium: { color: "var(--yellow)", bg: "var(--yellow-bg)", border: "var(--yellow-border)", label: "Sedang" },
    High: { color: "var(--orange)", bg: "var(--orange-bg)", border: "var(--orange-border)", label: "Tinggi" },
    Severe: { color: "var(--red)", bg: "var(--red-bg)", border: "var(--red-border)", label: "Parah" },
  };
  return map[level] ?? map["Low"];
};

const sigColor = (s: string) => {
  const v = s.toLowerCase();
  return v === "green" ? "var(--green)" : v === "yellow" ? "var(--yellow)" : "var(--red)";
};

export const IntersectionCard = ({
  intersection: ix,
  onClick,
  cameraData,
}: {
  intersection: Intersection;
  onClick?: () => void;
  cameraData?: any;
}) => {
  const { data: weather } = useWeatherByIntersection(ix.intersection_id);
  // Use cameraData prop if provided (from parent's useAllCameras), otherwise fetch individually
  const { data: fetchedCamera } = useCameraByIntersection(cameraData ? "" : ix.intersection_id);
  const camera = cameraData ?? fetchedCamera;

  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const b = badge(ix.occupancy_rate);
  const videoRetries = useRef(0);

  // Update video URL whenever camera data changes
  useEffect(() => {
    videoRetries.current = 0;
    setVideoUrl(buildVideoUrl(camera?.expected_video_url, camera?.video_exists));
  }, [camera?.expected_video_url, camera?.video_exists]);

  // Refresh video every 3 minutes (cache bust)
  useEffect(() => {
    const interval = setInterval(
      () => {
        videoRetries.current = 0;
        setVideoUrl(buildVideoUrl(camera?.expected_video_url, camera?.video_exists));
      },
      3 * 60 * 1000,
    );
    return () => clearInterval(interval);
  }, [camera?.expected_video_url, camera?.video_exists]);

  const weatherIcon: Record<string, string> = {
    Sunny: "☀️",
    Cloudy: "☁️",
    Rain: "🌧️",
    Storm: "⛈️",
  };

  return (
    <>
      <div
        onClick={onClick}
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border)",
          borderRadius: 10,
          overflow: "hidden",
          cursor: onClick ? "pointer" : "default",
          transition: "border-color .15s, transform .15s",
        }}
        onMouseEnter={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border-hover)";
          (e.currentTarget as HTMLDivElement).style.transform =
            "translateY(-1px)";
        }}
        onMouseLeave={(e) => {
          (e.currentTarget as HTMLDivElement).style.borderColor = "var(--border)";
          (e.currentTarget as HTMLDivElement).style.transform = "translateY(0)";
        }}
      >
        {/* CCTV Feed */}
        <div
          style={{
            height: 80,
            background: "var(--bg-elevated)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* REC badge */}
          <div
            style={{
              position: "absolute",
              top: 7,
              left: 7,
              zIndex: 2,
              display: "flex",
              alignItems: "center",
              gap: 3,
              fontSize: 11,
              fontWeight: 700,
              color: "var(--red)",
              background: "rgba(248,113,113,.1)",
              border: "1px solid rgba(248,113,113,.2)",
              padding: "2px 6px",
              borderRadius: 4,
            }}
          >
            <span
              style={{
                width: 4,
                height: 4,
                borderRadius: "50%",
                background: "var(--red)",
                display: "inline-block",
                animation: "blink 1s infinite",
              }}
            />
            REC
          </div>


          {/* Camera ID */}
          <div
            style={{
              position: "absolute",
              bottom: 6,
              left: 7,
              zIndex: 2,
              fontSize: 11,
              color: "#b0bec5",
              background: "rgba(0,0,0,.5)",
              padding: "1px 5px",
              borderRadius: 3,
            }}
          >
            {camera?.camera_id ??
              `CAM-${ix.intersection_id.replace("INT-", "")}`}
          </div>

          {/* Flow badge */}
          <div
            style={{
              position: "absolute",
              bottom: 6,
              right: 7,
              zIndex: 2,
              fontSize: 11,
              fontWeight: 600,
              color: b.color,
              background: b.bg,
              border: `1px solid ${b.border}`,
              padding: "1px 6px",
              borderRadius: 3,
            }}
          >
            {b.label}
          </div>

          {/* Video */}
          {videoUrl ? (
            <video
              src={videoUrl}
              autoPlay
              loop
              muted
              playsInline
              onError={() => {
                videoRetries.current += 1;
                if (videoRetries.current < 3) {
                  // Retry: re-fetch same URL with cache-bust
                  const base = buildVideoUrl(camera?.expected_video_url, camera?.video_exists);
                  setVideoUrl(base ? `${base}?t=${Date.now()}` : null);
                } else {
                  setVideoUrl(null);
                }
              }}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                opacity: 0.9,
              }}
            />
          ) : (
            <div
              style={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 4,
                opacity: 0.2,
              }}
            >
              <span style={{ fontSize: 22 }}>📷</span>
              <p style={{ fontSize: 11, color: "#7b8fa3" }}>No stream</p>
            </div>
          )}
        </div>

        <div style={{ padding: "10px 12px" }}>
          {/* Header */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: 8,
            }}
          >
            <div>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 2 }}>
                {ix.intersection_id}
              </p>
              <p style={{ fontSize: 15, fontWeight: 600, color: "var(--text-primary)" }}>
                {ix.intersection_name}
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: sigColor(ix.signal_state),
                  display: "inline-block",
                  boxShadow: `0 0 6px ${sigColor(ix.signal_state)}`,
                }}
              />
              {ix.congestion_level && ix.congestion_level !== "Low" && (() => {
                const cb = congestionBadge(ix.congestion_level);
                return (
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      padding: "2px 6px",
                      borderRadius: 4,
                      background: cb.bg,
                      color: cb.color,
                      border: `1px solid ${cb.border}`,
                    }}
                  >
                    {cb.label}
                  </span>
                );
              })()}
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  padding: "2px 7px",
                  borderRadius: 4,
                  background: b.bg,
                  color: b.color,
                  border: `1px solid ${b.border}`,
                }}
              >
                {b.label}
              </span>
            </div>
          </div>

          {/* Stats */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr",
              gap: 6,
              marginBottom: 10,
            }}
          >
            {[
              { label: "Kendaraan", val: camera?.traffic?.vehicle_count ?? ix.vehicle_count },
              { label: "Speed", val: `${(camera?.traffic?.avg_speed_kmh ?? ix.avg_speed).toFixed(0)} km/h` },
              { label: "Queue", val: camera?.traffic?.queue_length_veh ?? ix.queue_length },
            ].map(({ label, val }) => (
              <div
                key={label}
                style={{
                  background: "var(--bg-elevated)",
                  borderRadius: 7,
                  padding: "7px 8px",
                }}
              >
                <p style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 2 }}>
                  {label}
                </p>
                <p style={{ fontSize: 15, fontWeight: 600, color: "var(--text-secondary)" }}>
                  {val}
                </p>
              </div>
            ))}
          </div>

          {/* Occupancy bar */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 12,
              color: "var(--text-muted)",
              marginBottom: 4,
            }}
          >
            <span>Occupancy</span>
            <span style={{ color: b.color }}>
              {(ix.occupancy_rate * 100).toFixed(0)}%
            </span>
          </div>
          <div
            style={{
              height: 4,
              background: "var(--border)",
              borderRadius: 3,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                background: b.color,
                borderRadius: 3,
                width: `${ix.occupancy_rate * 100}%`,
                transition: "width .7s ease",
                boxShadow: `0 0 8px ${b.color}`,
              }}
            />
          </div>

          {/* AI Insight strip */}
          {ix.ai_insight && (
            <div
              style={{
                marginTop: 8,
                background: "rgba(167,139,250,.04)",
                border: "1px solid rgba(167,139,250,.08)",
                borderRadius: 6,
                padding: "5px 8px",
                display: "flex",
                alignItems: "flex-start",
                gap: 5,
              }}
            >
              <span style={{ fontSize: 12, flexShrink: 0 }}>🤖</span>
              <p
                style={{
                  fontSize: 11,
                  color: "var(--text-secondary)",
                  lineHeight: 1.45,
                  margin: 0,
                  overflow: "hidden",
                  display: "-webkit-box",
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: "vertical",
                }}
              >
                {ix.ai_insight}
              </p>
            </div>
          )}

          {/* Weather badge */}
          <div
            style={{
              marginTop: 8,
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 5,
                background: "var(--bg-elevated)",
                border: "1px solid var(--border)",
                borderRadius: 6,
                padding: "3px 8px",
              }}
            >
              <span style={{ fontSize: 13 }}>
                {weatherIcon[weather?.condition ?? ix.weather_condition] ??
                  "🌤️"}
              </span>
              <span style={{ fontSize: 13, color: "var(--text-secondary)", fontWeight: 600 }}>
                {weather?.temperature_celsius ?? "—"}°C
              </span>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                {weather?.humidity_percent ?? "—"}%
              </span>
            </div>
            <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
              🟢 {ix.green_duration_seconds}s
            </p>
          </div>
        </div>
      </div>
    </>
  );
};
