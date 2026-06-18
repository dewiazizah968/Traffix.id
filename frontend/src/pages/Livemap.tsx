import { useEffect, useRef, useState } from "react";
import { useIntersections } from "../hooks/useTraffixData";
import { getVideoUrl } from "../lib/videoMap";
import { PredictionChart } from "../components/dashboard/PredictionChart";
import type { Intersection } from "../types";

const COORDS: Record<string, [number, number]> = {
  "INT-001": [-6.1911513, 106.7441887], // GT Meruya 2B (CAM_001)
  "INT-002": [-6.2131428, 106.6837664], // KM 00+600 (CAM_002)
  "INT-003": [-6.2225065, 106.6394746], // KM 10+600 (CAM_003)
  "INT-004": [-6.2024517, 106.7052155], // KM 11+600 (CAM_004)
};

const badge = (rate: number) => {
  if (rate >= 0.75)
    return {
      color: "var(--red)",
      bg: "rgba(248,113,113,.1)",
      border: "rgba(248,113,113,.2)",
      label: "HEAVY",
    };
  if (rate >= 0.45)
    return {
      color: "var(--yellow)",
      bg: "rgba(251,191,36,.1)",
      border: "rgba(251,191,36,.2)",
      label: "MOD",
    };
  return {
    color: "var(--green)",
    bg: "rgba(74,222,128,.1)",
    border: "rgba(74,222,128,.2)",
    label: "OK",
  };
};

const sigColor = (s: string) => {
  const v = s.toLowerCase();
  return v === "green" ? "var(--green)" : v === "yellow" ? "var(--yellow)" : "var(--red)";
};

export const LiveMap = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<Record<string, any>>({});
  const { data: intersections = [] } = useIntersections();
  const [selected, setSelected] = useState<Intersection | null>(null);

  // Init map
  useEffect(() => {
    if (mapInstanceRef.current || !mapRef.current) return;
    const L = (window as any).L;
    if (!L) return;

    const map = L.map(mapRef.current, {
      center: [-6.2071, 106.6933], // tengah antara semua lokasi
      zoom: 12,
      zoomControl: true,
    });

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap",
    }).addTo(map);

    mapInstanceRef.current = map;
  }, []);

  // Update markers
  useEffect(() => {
    const L = (window as any).L;
    if (!L || !mapInstanceRef.current || !intersections.length) return;

    Object.values(markersRef.current).forEach((m: any) => m.remove());
    markersRef.current = {};

    intersections.forEach((ix) => {
      const coords = COORDS[ix.intersection_id] ?? [-6.1863, 106.7973];
      const b = badge(ix.occupancy_rate);

      const icon = L.divIcon({
        html: `<div style="
          width:16px;height:16px;border-radius:50%;
          background:${b.color};border:2.5px solid #0d1117;
          box-shadow:0 0 12px ${b.color}88;cursor:pointer;
        "></div>`,
        className: "",
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });

      const marker = L.marker(coords, { icon }).addTo(mapInstanceRef.current);

      // Hover tooltip
      const tooltipHtml = `
        <div style="min-width:160px">
          <div style="display:flex;align-items:center;gap:5px;margin-bottom:5px">
            <span style="width:6px;height:6px;border-radius:50%;background:${b.color};display:inline-block"></span>
            <strong style="font-size:12px;color:#f0f4ff">${ix.intersection_name}</strong>
          </div>
          <div style="font-size:10px;color:#6b7fa8;margin-bottom:6px">${ix.intersection_id} · ${ix.weather_condition}</div>
          <div style="display:flex;gap:6px">
            <div style="flex:1;background:rgba(255,255,255,.04);border-radius:4px;padding:3px 6px;text-align:center">
              <div style="font-size:8px;color:#5c6e8a">Kendaraan</div>
              <div style="font-size:12px;font-weight:600;color:#60a5fa">${ix.vehicle_count}</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,.04);border-radius:4px;padding:3px 6px;text-align:center">
              <div style="font-size:8px;color:#5c6e8a">Speed</div>
              <div style="font-size:12px;font-weight:600;color:#4ade80">${ix.avg_speed.toFixed(0)} km/h</div>
            </div>
            <div style="flex:1;background:rgba(255,255,255,.04);border-radius:4px;padding:3px 6px;text-align:center">
              <div style="font-size:8px;color:#5c6e8a">Status</div>
              <div style="font-size:10px;font-weight:600;color:${b.color}">${b.label}</div>
            </div>
          </div>
        </div>
      `;
      marker.bindTooltip(tooltipHtml, {
        direction: "top",
        offset: [0, -12],
        opacity: 1,
        className: "traffix-tooltip",
      });

      marker.on("click", () => {
        setSelected((prev) =>
          prev?.intersection_id === ix.intersection_id ? null : ix,
        );
        mapInstanceRef.current.setView(coords, 17, { animate: true });
      });

      markersRef.current[ix.intersection_id] = marker;
    });
  }, [intersections]);

  // Update marker saat selected berubah
  useEffect(() => {
    const L = (window as any).L;
    if (!L) return;
    intersections.forEach((ix) => {
      const marker = markersRef.current[ix.intersection_id];
      if (!marker) return;
      const b = badge(ix.occupancy_rate);
      const isSelected = selected?.intersection_id === ix.intersection_id;

      const icon = L.divIcon({
        html: `<div style="
          width:${isSelected ? 22 : 16}px;
          height:${isSelected ? 22 : 16}px;
          border-radius:50%;
          background:${b.color};
          border:${isSelected ? "3px solid #fff" : "2.5px solid #0d1117"};
          box-shadow:0 0 ${isSelected ? 20 : 10}px ${b.color};
          cursor:pointer;
        "></div>`,
        className: "",
        iconSize: [isSelected ? 22 : 16, isSelected ? 22 : 16],
        iconAnchor: [isSelected ? 11 : 8, isSelected ? 11 : 8],
      });
      marker.setIcon(icon);
    });
  }, [selected, intersections]);

  return (
    <div style={{ display: "flex", height: "100%", position: "relative" }}>
      {/* Dark map style */}
      <style>{`
        .leaflet-container { background: #0d1117 !important; }
        .leaflet-tile { filter: brightness(0.6) saturate(0.7) invert(1) hue-rotate(180deg); }
        .leaflet-control-zoom a {
          background: #0d1117 !important; color: #94a3b8 !important;
          border-color: #1e2736 !important;
        }
        .leaflet-control-attribution {
          background: rgba(13,17,23,.8) !important;
          color: #2d3f50 !important; font-size: 9px !important;
        }
        .traffix-tooltip {
          background: rgba(10,15,26,.95) !important;
          border: 1px solid rgba(59,130,246,.2) !important;
          border-radius: 10px !important;
          padding: 10px 12px !important;
          box-shadow: 0 12px 40px rgba(0,0,0,.6) !important;
          backdrop-filter: blur(12px);
          font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        .traffix-tooltip::before {
          border-top-color: rgba(10,15,26,.95) !important;
        }
      `}</style>

      {/* Map */}
      <div ref={mapRef} style={{ flex: 1, height: "100%" }} />

      {/* Legend */}
      <div
        style={{
          position: "absolute",
          top: 12,
          left: 12,
          zIndex: 1000,
          background: "rgba(13,17,23,.92)",
          border: "1px solid #1e2736",
          borderRadius: 10,
          padding: "10px 14px",
          backdropFilter: "blur(8px)",
        }}
      >
        <p
          style={{
            fontSize: 10,
            color: "var(--text-dim)",
            textTransform: "uppercase",
            letterSpacing: ".07em",
            marginBottom: 8,
          }}
        >
          Status Simpang
        </p>
        {[
          { color: "var(--green)", label: "Normal (OK)" },
          { color: "var(--yellow)", label: "Sedang (MOD)" },
          { color: "var(--red)", label: "Macet (HEAVY)" },
        ].map(({ color, label }) => (
          <div
            key={label}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              marginBottom: 5,
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: color,
                display: "inline-block",
                boxShadow: `0 0 6px ${color}`,
              }}
            />
            <span style={{ fontSize: 11, color: "#94a3b8" }}>{label}</span>
          </div>
        ))}
      </div>

      {/* Intersection count */}
      <div
        style={{
          position: "absolute",
          top: 12,
          right: 12,
          zIndex: 1000,
          background: "rgba(13,17,23,.92)",
          border: "1px solid #1e2736",
          borderRadius: 10,
          padding: "8px 14px",
          backdropFilter: "blur(8px)",
        }}
      >
        <p style={{ fontSize: 10, color: "var(--text-dim)" }}>Total Simpang</p>
        <p style={{ fontSize: 18, fontWeight: 600, color: "var(--stat-value)" }}>
          {intersections.length}
        </p>
      </div>

      {/* Unified Modal — same as Dashboard */}
      {selected &&
        (() => {
          const b = badge(selected.occupancy_rate);
          const sc = sigColor(selected.signal_state);
          const videoUrl = getVideoUrl(selected.intersection_id);

          return (
            <>
              {/* Backdrop */}
              <div
                onClick={() => setSelected(null)}
                style={{
                  position: "fixed",
                  inset: 0,
                  zIndex: 1000,
                  background: "rgba(0,0,0,.6)",
                  backdropFilter: "blur(8px)",
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
                  zIndex: 1001,
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-hover)",
                  borderRadius: 14,
                  overflow: "hidden",
                  boxShadow: "0 40px 100px rgba(0,0,0,.7)",
                  animation: "fadeIn .2s ease",
                  display: "grid",
                  gridTemplateColumns: "1fr 380px",
                }}
              >
                {/* ── LEFT: Video Feed ── */}
                <div style={{ position: "relative", background: "#0a0f1a", minHeight: 400 }}>
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
                        CAM-{selected.intersection_id.replace("INT-", "")}
                      </span>
                    </div>
                    <button
                      onClick={() => setSelected(null)}
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
                        { label: "Kendaraan", val: selected.vehicle_count, color: "var(--blue)" },
                        {
                          label: "Speed",
                          val: `${selected.avg_speed.toFixed(0)} km/h`,
                          color: "var(--green)",
                        },
                        { label: "Queue", val: selected.queue_length, color: "var(--yellow)" },
                        {
                          label: "Occupancy",
                          val: `${(selected.occupancy_rate * 100).toFixed(0)}%`,
                          color: b.color,
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
                          background: sc,
                          boxShadow: `0 0 8px ${sc}`,
                        }}
                      />
                      <p style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                        {selected.intersection_name}
                      </p>
                    </div>
                    <p style={{ fontSize: 11, color: "var(--text-dim)" }}>
                      {selected.intersection_id} · {selected.weather_condition}
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
                        <span style={{ color: b.color }}>
                          {(selected.occupancy_rate * 100).toFixed(0)}%
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
                            width: `${selected.occupancy_rate * 100}%`,
                            background: b.color,
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
                              color: sc,
                              textTransform: "capitalize",
                            }}
                          >
                            {selected.signal_state}
                          </p>
                        </div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <p style={{ fontSize: 9, color: "var(--text-muted)" }}>Green Duration</p>
                        <p style={{ fontSize: 16, fontWeight: 600, color: "var(--green)" }}>
                          {selected.green_duration_seconds}s
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
                        intersectionId={selected.intersection_id}
                        currentCount={selected.vehicle_count}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </>
          );
        })()}
    </div>
  );
};
