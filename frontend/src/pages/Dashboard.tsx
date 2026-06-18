import { useState, useEffect } from "react";
import {
  useIntersections,
  useRecommendations,
  useWeather,
  useSystemStatus,
  useAllCameras,
} from "../hooks/useTraffixData";
import { buildVideoUrl } from "../lib/videoMap";
import { MetricCard } from "../components/dashboard/MetricCard";
import { IntersectionCard } from "../components/dashboard/IntersectionCard";
import { RecommendationPanel } from "../components/dashboard/RecommendationPanel";
import { PredictionChart } from "../components/dashboard/PredictionChart";
import type { Intersection } from "../types";
import { ManualSignalAdjust } from "../components/dashboard/ManualSignalAdjust";

export const Dashboard = () => {
  const { data: intersections = [], isLoading } = useIntersections();
  const { data: recommendations = [] } = useRecommendations();
  const { data: weather } = useWeather();
  const { data: status } = useSystemStatus();
  const [selected, setSelected] = useState<Intersection | null>(null);

  // Fetch all camera data in a single request
  const { camerasMap, cameras: allCameras } = useAllCameras();

  const totalVehicles = allCameras.length
    ? allCameras.reduce(
        (s, c) => s + (c?.traffic?.vehicle_count ?? 0),
        0,
      )
    : intersections.reduce((s, i) => s + i.vehicle_count, 0);
  const avgSpeed = allCameras.length
    ? (
        allCameras.reduce((s, c) => s + (c?.traffic?.avg_speed_kmh ?? 0), 0) /
        allCameras.length
      ).toFixed(0)
    : intersections.length
      ? (
          intersections.reduce((s, i) => s + i.avg_speed, 0) /
          intersections.length
        ).toFixed(0)
      : "—";
  const topRec = recommendations[0];

  if (isLoading)
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100%",
          color: "var(--text-muted)",
          fontSize: 12,
        }}
      >
        <span style={{ animation: "pulse 1.5s infinite" }}>
          Connecting to backend...
        </span>
      </div>
    );

  return (
    <div
      style={{
        padding: "14px 16px",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        overflowY: "auto",
        height: "100%",
      }}
    >
      {/* ── Row 1: Metrics ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4,1fr)",
          gap: 10,
        }}
      >
        <MetricCard
          label="Total Kendaraan"
          icon="🚗"
          value={totalVehicles}
          sub={`${intersections.length} simpang aktif`}
          accent="blue"
        />
        <MetricCard
          label="Avg Speed"
          icon="⚡"
          value={`${avgSpeed} km/h`}
          sub="Rata-rata semua lane"
          accent="green"
        />
        <MetricCard
          label="Active Recs"
          icon="🤖"
          value={recommendations.length}
          sub={topRec ? `${topRec.priority} priority` : "Semua normal"}
          accent="orange"
        />
        <MetricCard
          label="Weather"
          icon="🌤"
          value={weather?.condition ?? "—"}
          sub={
            weather?.temperature_celsius
              ? `${weather.temperature_celsius}°C · ${weather.humidity_percent}%`
              : (status?.ml_mode ?? "fallback")
          }
          accent="purple"
        />
      </div>

      {/* ── Row 2: Main Content ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 320px",
          gap: 12,
          flex: 1,
          minHeight: 0,
        }}
      >
        {/* ── Left: Intersection Grid ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8, minHeight: 0 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <p
              style={{
                fontSize: 11,
                color: "var(--text-dim)",
                textTransform: "uppercase",
                letterSpacing: ".08em",
              }}
            >
              Live Intersections
            </p>
            <p style={{ fontSize: 10, color: "var(--text-muted)" }}>
              Klik untuk detail & prediksi
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
              gap: 10,
              flex: 1,
            }}
          >
            {intersections.map((ix) => (
              <IntersectionCard
                key={ix.intersection_id}
                intersection={ix}
                onClick={() => setSelected(ix)}
                cameraData={camerasMap[ix.intersection_id]}
              />
            ))}
          </div>
        </div>

        {/* ── Right: Sidebar ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {/* Recommendation */}
          {topRec ? (
            <RecommendationPanel />
          ) : (
            <div
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                borderRadius: 12,
                padding: 24,
                textAlign: "center",
              }}
            >
              <p style={{ fontSize: 22, marginBottom: 8 }}>✅</p>
              <p style={{ fontSize: 13, color: "var(--green)", fontWeight: 500 }}>
                All Clear
              </p>
              <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                Tidak ada rekomendasi aktif
              </p>
            </div>
          )}

          {/* System status */}
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: 14,
            }}
          >
            <p
              style={{
                fontSize: 10,
                color: "var(--text-dim)",
                textTransform: "uppercase",
                letterSpacing: ".08em",
                marginBottom: 12,
              }}
            >
              System Status
            </p>
            {[
              { label: "ML Model", ok: status?.ml_ready },
              { label: "Simulation", ok: status?.simulation_active },
              { label: "Dataset", ok: status?.dataset_ready },
              { label: "Weather", ok: status?.weather_ready },
            ].map(({ label, ok }) => (
              <div
                key={label}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 8,
                }}
              >
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{label}</span>
                <span
                  style={{
                    fontSize: 9,
                    fontWeight: 600,
                    padding: "2px 8px",
                    borderRadius: 20,
                    background: ok
                      ? "rgba(74,222,128,.08)"
                      : "rgba(71,85,105,.08)",
                    color: ok ? "var(--green)" : "var(--text-dim)",
                    border: `1px solid ${ok ? "rgba(74,222,128,.2)" : "rgba(71,85,105,.2)"}`,
                  }}
                >
                  {ok ? "ACTIVE" : "IDLE"}
                </span>
              </div>
            ))}

            {/* Fail-safe */}
            <div
              style={{
                marginTop: 10,
                background: "var(--bg-elevated)",
                borderRadius: 8,
                padding: "9px 11px",
                display: "flex",
                gap: 7,
                alignItems: "flex-start",
                border: "1px solid var(--border)",
              }}
            >
              <span style={{ fontSize: 13, color: "var(--green)" }}>🛡</span>
              <p style={{ fontSize: 10, color: "var(--text-dim)", lineHeight: 1.55 }}>
                <span style={{ color: "var(--text-muted)", fontWeight: 500 }}>
                  Fail-safe aktif
                </span>{" "}
                — auto-switch ke local timer jika API terputus &gt;60 detik
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Modal */}
      {selected && (
        <PredictionModal ix={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
};

/* ── Unified Modal: Video + Stats + Chart ── */
const PredictionModal = ({
  ix,
  onClose,
}: {
  ix: Intersection;
  onClose: () => void;
}) => {
  const { camerasMap } = useAllCameras();
  const camera = camerasMap[ix.intersection_id];
  const videoUrl = buildVideoUrl(camera?.expected_video_url, camera?.video_exists);

  useEffect(() => {
    const fn = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, [onClose]);

  const sigCol = (s: string) => {
    const v = s.toLowerCase();
    return v === "green" ? "var(--green)" : v === "yellow" ? "var(--yellow)" : "var(--red)";
  };

  const occRate = camera?.traffic?.density_percent != null
    ? camera.traffic.density_percent / 100
    : ix.occupancy_rate;
  const occColor =
    occRate >= 0.75 ? "var(--red)" : occRate >= 0.45 ? "var(--yellow)" : "var(--green)";

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "var(--overlay-heavy)",
          backdropFilter: "blur(8px)",
          zIndex: 100,
        }}
      />

      {/* Modal */}
      <div
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%,-50%)",
          width: "min(1100px, 96vw)",
          maxHeight: "92vh",
          zIndex: 101,
          background: "var(--bg-card)",
          border: "1px solid var(--border-hover)",
          borderRadius: 14,
          overflow: "hidden",
          boxShadow: "0 40px 100px var(--shadow)",
          animation: "fadeIn .2s ease",
          display: "grid",
          gridTemplateColumns: "1fr 380px",
        }}
      >
        {/* ── LEFT: Video Feed ── */}
        <div style={{ position: "relative", background: "var(--bg-base)", minHeight: 400 }}>
          {/* Top overlay */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              zIndex: 2,
              padding: "10px 14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: "linear-gradient(rgba(0,0,0,.7), transparent)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  fontSize: 11,
                  fontWeight: 700,
                  color: "var(--red)",
                  background: "rgba(248,113,133,.15)",
                  border: "1px solid rgba(248,113,133,.3)",
                  padding: "3px 8px",
                  borderRadius: 4,
                }}
              >
                <span
                  style={{
                    width: 5,
                    height: 5,
                    borderRadius: "50%",
                    background: "var(--red)",
                    display: "inline-block",
                    animation: "blink 1s infinite",
                  }}
                />
                LIVE
              </div>
              <span style={{ fontSize: 12, color: "#e0e6ed", fontWeight: 500 }}>
                {camera?.camera_id ?? `CAM-${ix.intersection_id.replace("INT-", "")}`}
              </span>
            </div>
            <button
              onClick={onClose}
              style={{
                width: 28,
                height: 28,
                borderRadius: 7,
                background: "rgba(0,0,0,.5)",
                border: "1px solid rgba(255,255,255,.1)",
                color: "#94a3b8",
                fontSize: 14,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              ✕
            </button>
          </div>

          {/* Video */}
          {videoUrl ? (
            <video
              src={videoUrl}
              autoPlay
              loop
              muted
              playsInline
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                gap: 8,
                opacity: 0.15,
              }}
            >
              <span style={{ fontSize: 56 }}>📷</span>
              <p style={{ fontSize: 14, color: "var(--text-muted)" }}>
                Stream tidak tersedia
              </p>
            </div>
          )}

          {/* Bottom stats overlay */}
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              zIndex: 2,
              padding: "16px 14px 10px",
              background: "linear-gradient(transparent, rgba(0,0,0,.85))",
            }}
          >
            <div style={{ display: "flex", gap: 6 }}>
              {[
                { label: "Kendaraan", val: camera?.traffic?.vehicle_count ?? ix.vehicle_count, color: "var(--blue)" },
                {
                  label: "Speed",
                  val: `${(camera?.traffic?.avg_speed_kmh ?? ix.avg_speed).toFixed(0)} km/h`,
                  color: "var(--green)",
                },
                { label: "Queue", val: camera?.traffic?.queue_length_veh ?? ix.queue_length, color: "var(--yellow)" },
                {
                  label: "Occupancy",
                  val: `${(occRate * 100).toFixed(0)}%`,
                  color: occColor,
                },
              ].map(({ label, val, color }) => (
                <div
                  key={label}
                  style={{
                    background: "rgba(0,0,0,.5)",
                    border: "1px solid rgba(255,255,255,.06)",
                    borderRadius: 7,
                    padding: "5px 10px",
                    flex: 1,
                    textAlign: "center",
                  }}
                >
                  <p style={{ fontSize: 10, color: "#8899b8", marginBottom: 2 }}>
                    {label}
                  </p>
                  <p style={{ fontSize: 15, fontWeight: 600, color }}>{val}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── RIGHT: Info Panel ── */}
        <div
          style={{
            overflowY: "auto",
            maxHeight: "92vh",
            borderLeft: "1px solid var(--border)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "14px 16px",
              borderBottom: "1px solid var(--border)",
              position: "sticky",
              top: 0,
              background: "var(--bg-card)",
              zIndex: 1,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 2 }}>
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: "50%",
                  display: "inline-block",
                  background: sigCol(ix.signal_state),
                  boxShadow: `0 0 8px ${sigCol(ix.signal_state)}`,
                }}
              />
              <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                {ix.intersection_name}
              </p>
            </div>
            <p style={{ fontSize: 11, color: "var(--text-dim)" }}>
              {ix.intersection_id} · {ix.weather_condition}
            </p>
          </div>

          {/* Content */}
          <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 12, flex: 1 }}>
            {/* Occupancy bar */}
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 10,
                  color: "var(--text-muted)",
                  marginBottom: 4,
                }}
              >
                <span>Occupancy Rate</span>
                <span style={{ color: occColor }}>
                  {(occRate * 100).toFixed(0)}%
                </span>
              </div>
              <div
                style={{
                  height: 4,
                  background: "var(--border)",
                  borderRadius: 4,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    borderRadius: 4,
                    transition: "width .7s ease",
                    width: `${occRate * 100}%`,
                    background: occColor,
                  }}
                />
              </div>
            </div>

            {/* Signal info */}
            <div
              style={{
                background: "var(--bg-elevated)",
                borderRadius: 8,
                padding: 10,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                <span>🚦</span>
                <div>
                  <p style={{ fontSize: 9, color: "var(--text-muted)" }}>Signal</p>
                  <p
                    style={{
                      fontSize: 12,
                      fontWeight: 500,
                      color: sigCol(ix.signal_state),
                      textTransform: "capitalize",
                    }}
                  >
                    {ix.signal_state}
                  </p>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ fontSize: 9, color: "var(--text-muted)" }}>Green Duration</p>
                <p style={{ fontSize: 16, fontWeight: 600, color: "var(--green)" }}>
                  {ix.green_duration_seconds}s
                </p>
              </div>
            </div>

            {/* Prediction Chart */}
            <div>
              <p
                style={{
                  fontSize: 10,
                  color: "var(--text-dim)",
                  textTransform: "uppercase",
                  letterSpacing: ".07em",
                  marginBottom: 6,
                }}
              >
                Prediksi LSTM
              </p>
              <PredictionChart
                intersectionId={ix.intersection_id}
                currentCount={ix.vehicle_count}
              />
            </div>

            {/* Manual Adjustment */}
            <div>
              <p
                style={{
                  fontSize: 10,
                  color: "var(--text-dim)",
                  textTransform: "uppercase",
                  letterSpacing: ".07em",
                  marginBottom: 6,
                }}
              >
                Kontrol Manual
              </p>
              <ManualSignalAdjust intersection={ix} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

