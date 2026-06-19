import { useState, useEffect } from "react";
import {
  useRecommendations,
  useIntersections,
  useSimulation,
} from "../../hooks/useTraffixData";

type Act = "idle" | "approved" | "rejected" | "simulating";

const stateMap = {
  idle: {
    bg: "rgba(251,191,36,.07)",
    border: "rgba(251,191,36,.15)",
    icon: "⚠️",
    title: "Risiko Kemacetan Terdeteksi",
    tc: "var(--yellow)",
  },
  approved: {
    bg: "rgba(74,222,128,.07)",
    border: "rgba(74,222,128,.15)",
    icon: "✓",
    title: "Rekomendasi Disetujui",
    tc: "var(--green)",
  },
  rejected: {
    bg: "rgba(71,85,105,.07)",
    border: "rgba(71,85,105,.15)",
    icon: "✕",
    title: "Rekomendasi Ditolak",
    tc: "#64748b",
  },
  simulating: {
    bg: "rgba(37,99,235,.07)",
    border: "rgba(37,99,235,.15)",
    icon: "▶",
    title: "Mode Simulasi Aktif",
    tc: "var(--blue)",
  },
};

// Priority → warna badge
const priorityStyle: Record<
  string,
  { color: string; bg: string; border: string }
> = {
  LOW: {
    color: "var(--green)",
    bg: "rgba(74,222,128,.1)",
    border: "rgba(74,222,128,.2)",
  },
  MEDIUM: {
    color: "var(--yellow)",
    bg: "rgba(251,191,36,.1)",
    border: "rgba(251,191,36,.2)",
  },
  HIGH: {
    color: "var(--orange)",
    bg: "rgba(251,146,60,.1)",
    border: "rgba(251,146,60,.2)",
  },
  CRITICAL: {
    color: "var(--red)",
    bg: "rgba(248,113,113,.1)",
    border: "rgba(248,113,113,.2)",
  },
};

import type { SimulationResult } from "../../types";

const congestionColor: Record<string, string> = {
  Low: "var(--green)",
  Medium: "var(--yellow)",
  High: "var(--orange)",
  Severe: "var(--red)",
};

const MetricRow = ({
  icon,
  label: _label,
  before,
  after,
  unit,
  changePct,
  improved,
}: {
  icon: string;
  label: string;
  before: string | number;
  after: string | number;
  unit: string;
  changePct: number;
  improved: boolean;
}) => (
  <div
    style={{
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 6,
      padding: "5px 0",
      borderBottom: "1px solid var(--border)",
    }}
  >
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <span style={{ fontSize: 11 }}>{icon}</span>
      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
        {before}
        {unit}
      </span>
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      <span style={{ fontSize: 11, color: "var(--stat-value)", fontWeight: 600 }}>
        {after}
        {unit}
      </span>
      {changePct !== 0 && (
        <span
          style={{
            fontSize: 9,
            fontWeight: 600,
            padding: "1px 5px",
            borderRadius: 4,
            background: improved
              ? "rgba(74,222,128,.1)"
              : "rgba(248,113,113,.1)",
            color: improved ? "var(--green)" : "var(--red)",
          }}
        >
          {improved ? "▼" : "▲"} {Math.abs(changePct).toFixed(0)}%
        </span>
      )}
    </div>
  </div>
);

const SimulationPanel = ({ sim }: { sim: SimulationResult }) => {
  const riskDrop = sim.risk_before - sim.risk_after;
  const curColor = congestionColor[sim.current.congestion_level] ?? "var(--text-muted)";
  const projColor =
    congestionColor[sim.projected.congestion_level] ?? "var(--text-muted)";

  return (
    <div
      style={{
        background: "rgba(37,99,235,.05)",
        border: "1px solid rgba(37,99,235,.15)",
        borderRadius: 8,
        padding: 12,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: 11, fontWeight: 600, color: "var(--blue)" }}>
          ▶ Proyeksi Dampak Simulasi
        </span>
        <span
          style={{
            fontSize: 9,
            padding: "2px 6px",
            borderRadius: 4,
            background: "rgba(37,99,235,.15)",
            color: "var(--blue)",
            fontWeight: 600,
          }}
        >
          +{sim.delta_seconds}s hijau
        </span>
      </div>

      {/* Column Headers */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 6,
          paddingBottom: 4,
          borderBottom: "1px solid rgba(37,99,235,.15)",
        }}
      >
        <span style={{ fontSize: 9, color: "var(--text-dim)", fontWeight: 600 }}>
          SAAT INI
        </span>
        <span style={{ fontSize: 9, color: "var(--blue)", fontWeight: 600 }}>
          PROYEKSI
        </span>
      </div>

      {/* Metrics */}
      <MetricRow
        icon="⏱"
        label="Speed"
        before={sim.current.avg_speed}
        after={sim.projected.avg_speed}
        unit=" km/h"
        changePct={sim.improvements.speed_gain_pct}
        improved={true}
      />
      <MetricRow
        icon="📏"
        label="Queue"
        before={sim.current.queue_length}
        after={sim.projected.queue_length}
        unit=" kend."
        changePct={sim.improvements.queue_reduction_pct}
        improved={true}
      />

      {/* Congestion Level Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 6,
          padding: "5px 0",
          borderBottom: "1px solid #161d27",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ fontSize: 11 }}>📊</span>
          <span
            style={{
              fontSize: 10,
              fontWeight: 600,
              padding: "1px 6px",
              borderRadius: 4,
              background: `${curColor}15`,
              color: curColor,
              border: `1px solid ${curColor}30`,
            }}
          >
            {sim.current.congestion_level}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span
            style={{
              fontSize: 10,
              fontWeight: 600,
              padding: "1px 6px",
              borderRadius: 4,
              background: `${projColor}15`,
              color: projColor,
              border: `1px solid ${projColor}30`,
            }}
          >
            {sim.projected.congestion_level}
          </span>
          {sim.current.congestion_level !== sim.projected.congestion_level && (
            <span style={{ fontSize: 9, color: "var(--green)" }}>✓</span>
          )}
        </div>
      </div>

      {/* Risk Comparison */}
      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: 10, color: "var(--text-dim)" }}>Risiko</span>
          <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
            {sim.risk_before.toFixed(0)}%{" "}
            <span style={{ color: "var(--blue)" }}>→</span>{" "}
            <span style={{ color: riskDrop > 0 ? "var(--green)" : "var(--text-muted)" }}>
              {sim.risk_after.toFixed(0)}%
            </span>
            {riskDrop > 0 && (
              <span
                style={{
                  fontSize: 9,
                  color: "var(--green)",
                  marginLeft: 4,
                  fontWeight: 600,
                }}
              >
                ▼{riskDrop.toFixed(0)}%
              </span>
            )}
          </span>
        </div>
        {/* Before bar */}
        <div
          style={{
            height: 3,
            background: "var(--border)",
            borderRadius: 3,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${sim.risk_before}%`,
              background: "var(--orange)",
              borderRadius: 3,
              transition: "width .5s ease",
              opacity: 0.5,
            }}
          />
        </div>
        {/* After bar */}
        <div
          style={{
            height: 3,
            background: "var(--border)",
            borderRadius: 3,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${sim.risk_after}%`,
              background: "var(--blue)",
              borderRadius: 3,
              boxShadow: "0 0 6px rgba(96,165,250,.4)",
              transition: "width .5s ease",
            }}
          />
        </div>
      </div>

      {/* Throughput badge */}
      {sim.improvements.throughput_gain_pct > 0 && (
        <div
          style={{
            textAlign: "center",
            fontSize: 10,
            color: "var(--green)",
            background: "rgba(74,222,128,.06)",
            borderRadius: 6,
            padding: "4px 8px",
            border: "1px solid rgba(74,222,128,.12)",
          }}
        >
          Est. throughput:{" "}
          <strong>+{sim.improvements.throughput_gain_pct.toFixed(0)}%</strong>{" "}
          kendaraan/siklus
        </div>
      )}

      {/* Summary */}
      <p style={{ fontSize: 10, color: "var(--text-dim)", lineHeight: 1.5 }}>
        {sim.summary}
      </p>
    </div>
  );
};



export const RecommendationPanel = () => {
  const { data: recommendations = [] } = useRecommendations();
  const { data: intersections = [] } = useIntersections();
  const [act, setAct] = useState<Act>("idle");

  // Otomatis pilih simpang paling kritis yang butuh perpanjangan hijau
  const rec = recommendations.find(
    (r) => r.priority !== "LOW" && r.delta_seconds > 0,
  ) ?? recommendations[0] ?? null;

  const needsAction = rec != null && rec.priority !== "LOW" && rec.delta_seconds > 0;

  // Fetch simulation data only when in simulating mode
  const { data: simData } = useSimulation(
    rec?.intersection_id ?? null,
    act === "simulating" && needsAction,
  );

  const [currentGreen, setCurrentGreen] = useState(
    rec?.current_green_seconds ?? 0,
  );

  useEffect(() => {
    if (rec && act === "idle") {
      setCurrentGreen(rec.current_green_seconds);
      setAct("idle");
    }
  }, [rec?.intersection_id, rec?.current_green_seconds]);

  // Ambil nama intersection dari intersection state
  const intersectionName = rec
    ? (intersections.find((i) => i.intersection_id === rec.intersection_id)
        ?.intersection_name ?? rec.intersection_id)
    : "";

  const idleState = !needsAction
    ? {
        bg: "rgba(74,222,128,.07)",
        border: "rgba(74,222,128,.15)",
        icon: "✅",
        title: "Lalu Lintas Terkendali",
        tc: "var(--green)",
      }
    : {
        bg: "rgba(251,191,36,.07)",
        border: "rgba(251,191,36,.15)",
        icon: "⚠️",
        title: "Risiko Kemacetan Terdeteksi",
        tc: "var(--yellow)",
      };

  const s = act === "idle" ? idleState : stateMap[act as keyof typeof stateMap];
  const ps = priorityStyle[rec?.priority ?? "LOW"];

  const desc: Record<Act, string> = {
    idle: rec?.reason ?? "",
    approved: `Durasi lampu hijau berhasil diperbarui menjadi ${rec?.recommended_green_seconds} detik. Sistem memantau dampak.`,
    rejected: `Operator menolak rekomendasi. Pertahankan fase hijau ${rec?.current_green_seconds} detik.`,
    simulating: `Simulasi aktif — proyeksi dampak penambahan ${rec?.delta_seconds ?? 0} detik tanpa eksekusi nyata.`,
  };

  const handleAction = (action: Act) => {
    setAct(action);
    if (action === "approved" && rec)
      setCurrentGreen(rec.recommended_green_seconds);
    if (action === "rejected" && rec)
      setCurrentGreen(rec.current_green_seconds);
  };

  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <span
          style={{
            fontSize: 12,
            fontWeight: 500,
            color: "var(--text-secondary)",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span>🤖</span> Rekomendasi AI
        </span>
        <span
            style={{
              fontSize: 9,
              fontWeight: 600,
              letterSpacing: ".06em",
              color: "#2563eb",
              background: "rgba(37,99,235,.1)",
              border: "1px solid rgba(37,99,235,.2)",
              padding: "2px 8px",
              borderRadius: 20,
            }}
          >
            AI AKTIF
          </span>
      </div>

      <div
        style={{
          padding: 16,
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        {!needsAction ? (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <p style={{ fontSize: 22, marginBottom: 8 }}>✅</p>
            <p style={{ fontSize: 13, color: "var(--green)", fontWeight: 500 }}>
              Semua Simpang Normal
            </p>
          </div>
        ) : (
          <>
            {/* Location + priority + congestion level */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                background: "var(--bg-elevated)",
                borderRadius: 8,
                padding: "8px 10px",
              }}
            >
              <div>
                <p style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 1 }}>
                  {rec.intersection_id}
                </p>
                <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                  {intersectionName}
                </p>
              </div>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-end",
                  gap: 4,
                }}
              >
                <span
                    style={{
                      fontSize: 9,
                      fontWeight: 600,
                      padding: "2px 7px",
                      borderRadius: 4,
                      background: ps.bg,
                      color: ps.color,
                      border: `1px solid ${ps.border}`,
                    }}
                  >
                    {rec.priority}
                  </span>
                <span style={{ fontSize: 10, color: "var(--text-dim)" }}>
                  Risiko: {rec.congestion_risk_percent.toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Congestion risk bar */}
            <div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 10,
                  color: "var(--text-dim)",
                  marginBottom: 5,
                }}
              >
                <span>Tingkat Risiko Kemacetan</span>
                <span style={{ color: ps.color }}>
                  {rec.congestion_risk_percent.toFixed(1)}%
                </span>
              </div>
              <div
                style={{
                  height: 3,
                  background: "var(--border)",
                  borderRadius: 3,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    borderRadius: 3,
                    width: `${rec.congestion_risk_percent}%`,
                    background: ps.color,
                    boxShadow: `0 0 8px ${ps.color}`,
                    transition: "width .7s ease",
                  }}
                />
              </div>
            </div>

            {/* AI Insight box / Simulation panel */}
            {act === "simulating" && simData ? (
              <SimulationPanel sim={simData} />
            ) : (
              <div
                style={{
                  background: s.bg,
                  border: `1px solid ${s.border}`,
                  borderRadius: 8,
                  padding: 11,
                }}
              >
                <p
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    color: s.tc,
                    marginBottom: 3,
                  }}
                >
                  {s.icon} {s.title}
                </p>
                <p style={{ fontSize: 11, color: "var(--text-dim)", lineHeight: 1.55 }}>
                  {desc[act]}
                </p>
              </div>
            )}


            {/* Signal comparison */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}
            >
              <div
                style={{ background: "var(--bg-elevated)", borderRadius: 8, padding: 10 }}
              >
                <p style={{ fontSize: 9, color: "var(--text-dim)", marginBottom: 4 }}>
                  Hijau Saat Ini
                </p>
                <p
                  style={{
                    fontSize: 20,
                    fontWeight: 600,
                    lineHeight: 1,
                    color: act === "approved" ? "var(--green)" : "var(--text-secondary)",
                    transition: "color .3s",
                  }}
                >
                  {currentGreen}
                  <span style={{ fontSize: 11, color: "var(--text-dim)" }}>s</span>
                  {act === "approved" && rec.delta_seconds && (
                    <span
                      style={{ fontSize: 11, color: "var(--green)", marginLeft: 6 }}
                    >
                      ▲ +{rec.delta_seconds}s
                    </span>
                  )}
                </p>
              </div>
              <div
                style={{ background: "var(--bg-elevated)", borderRadius: 8, padding: 10 }}
              >
                <p style={{ fontSize: 9, color: "var(--text-dim)", marginBottom: 4 }}>
                  Rekomendasi
                </p>
                <p
                  style={{
                    fontSize: 20,
                    fontWeight: 600,
                    lineHeight: 1,
                    color: act === "approved" ? "var(--text-dim)" : "var(--blue)",
                    transition: "color .3s",
                  }}
                >
                  {rec.recommended_green_seconds}
                  <span style={{ fontSize: 11, color: "var(--text-dim)" }}>s</span>
                  {act === "approved" && (
                    <span
                      style={{ fontSize: 10, color: "var(--text-dim)", marginLeft: 6 }}
                    >
                      ✓ diterapkan
                    </span>
                  )}
                </p>
              </div>
            </div>

            {/* Source label */}
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span
                style={{
                  fontSize: 9,
                  color: "var(--text-dim)",
                  fontStyle: "italic",
                }}
              >
                Sumber:{" "}
                <span
                  style={{
                    color: "var(--blue)",
                    fontWeight: 600,
                  }}
                >
                  YOLO + LSTM AI Engine
                </span>
              </span>
            </div>

            {/* Actions */}
            {rec.priority !== "LOW" && rec.delta_seconds > 0 && (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 6,
                }}
              >
                {[
                  {
                    label: "✓ Setujui",
                    action: "approved" as Act,
                    bg: "rgba(74,222,128,.08)",
                    color: "var(--green)",
                    border: "rgba(74,222,128,.2)",
                  },
                  {
                    label: "▶ Simulasi",
                    action: "simulating" as Act,
                    bg: "rgba(37,99,235,.08)",
                    color: "var(--blue)",
                    border: "rgba(37,99,235,.2)",
                  },
                  {
                    label: "✕ Tolak",
                    action: "rejected" as Act,
                    bg: "rgba(248,113,113,.08)",
                    color: "var(--red)",
                    border: "rgba(248,113,113,.2)",
                  },
                ].map((btn) => (
                  <button
                    key={btn.action}
                    onClick={() => handleAction(btn.action)}
                    style={{
                      padding: "8px 0",
                      fontSize: 11,
                      fontWeight: 600,
                      background: act === btn.action ? btn.bg : "transparent",
                      color: btn.color,
                      border: `1px solid ${act === btn.action ? btn.border : "var(--border)"}`,
                      borderRadius: 7,
                      cursor: "pointer",
                      transition: "all .15s",
                      opacity: act === btn.action ? 1 : 0.6,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.opacity =
                        act === btn.action ? "1" : "0.6")
                    }
                  >
                    {btn.label}
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
