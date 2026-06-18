import { useState } from "react";
import {
  useSystemStatus,
  useSimulationControls,
} from "../hooks/useTraffixData";

export const Settings = () => {
  const { data: status } = useSystemStatus();
  const { start, stop } = useSimulationControls();
  const [tickInterval, setTickInterval] = useState(2);
  const [maxIntersections, setMaxIntersections] = useState(4);

  const Section = ({
    title,
    children,
  }: {
    title: string;
    children: React.ReactNode;
  }) => (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid #161d27",
        borderRadius: 12,
        overflow: "hidden",
        marginBottom: 12,
      }}
    >
      <div
        style={{
          padding: "11px 16px",
          borderBottom: "1px solid #161d27",
          background: "var(--bg-elevated)",
        }}
      >
        <p
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "#94a3b8",
            textTransform: "uppercase",
            letterSpacing: ".06em",
          }}
        >
          {title}
        </p>
      </div>
      <div style={{ padding: 16 }}>{children}</div>
    </div>
  );

  const Row = ({
    label,
    sub,
    children,
  }: {
    label: string;
    sub?: string;
    children: React.ReactNode;
  }) => (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "10px 0",
        borderBottom: "1px solid #161d27",
      }}
    >
      <div>
        <p style={{ fontSize: 12, color: "var(--text-secondary)" }}>{label}</p>
        {sub && (
          <p style={{ fontSize: 10, color: "var(--text-dim)", marginTop: 1 }}>{sub}</p>
        )}
      </div>
      {children}
    </div>
  );

  return (
    <div style={{ padding: 20, maxWidth: 560, overflowY: "auto" }}>
      <p
        style={{
          fontSize: 15,
          fontWeight: 600,
          color: "var(--stat-value)",
          marginBottom: 16,
          letterSpacing: "-.3px",
        }}
      >
        Konfigurasi Sistem
      </p>

      {/* Simulation */}
      <Section title="Simulasi">
        <Row
          label="Status Engine"
          sub={
            status?.simulation_active
              ? "Simulasi berjalan"
              : "Simulasi berhenti"
          }
        >
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => start.mutate()}
              disabled={status?.simulation_active || start.isPending}
              style={{
                padding: "7px 14px",
                fontSize: 11,
                fontWeight: 600,
                borderRadius: 7,
                cursor: "pointer",
                background: "rgba(74,222,128,.08)",
                color: "var(--green)",
                border: "1px solid rgba(74,222,128,.2)",
                opacity: status?.simulation_active || start.isPending ? 0.4 : 1,
              }}
            >
              {start.isPending ? "Memulai..." : "▶ Mulai"}
            </button>
            <button
              onClick={() => stop.mutate()}
              disabled={!status?.simulation_active || stop.isPending}
              style={{
                padding: "7px 14px",
                fontSize: 11,
                fontWeight: 600,
                borderRadius: 7,
                cursor: "pointer",
                background: "rgba(248,113,113,.08)",
                color: "var(--red)",
                border: "1px solid rgba(248,113,113,.2)",
                opacity: !status?.simulation_active || stop.isPending ? 0.4 : 1,
              }}
            >
              {stop.isPending ? "Menghentikan..." : "■ Hentikan"}
            </button>
          </div>
        </Row>

        <Row label="Tick Interval" sub="Interval update data simulasi (detik)">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="number"
              min={1}
              max={10}
              value={tickInterval}
              onChange={(e) => setTickInterval(Number(e.target.value))}
              style={{
                width: 60,
                padding: "5px 8px",
                borderRadius: 6,
                background: "var(--bg-elevated)",
                border: "1px solid #1e2736",
                color: "var(--stat-value)",
                fontSize: 12,
                textAlign: "center",
                outline: "none",
              }}
            />
            <span style={{ fontSize: 11, color: "var(--text-dim)" }}>detik</span>
          </div>
        </Row>

        <Row
          label="Jumlah Simpang"
          sub="Jumlah intersection yang disimulasikan"
        >
          <div style={{ display: "flex", gap: 6 }}>
            {[2, 4, 6, 8].map((n) => (
              <button
                key={n}
                onClick={() => setMaxIntersections(n)}
                style={{
                  width: 32,
                  height: 28,
                  fontSize: 11,
                  borderRadius: 6,
                  cursor: "pointer",
                  background:
                    maxIntersections === n ? "rgba(37,99,235,.1)" : "var(--bg-elevated)",
                  color: maxIntersections === n ? "var(--blue)" : "var(--text-dim)",
                  border: `1px solid ${maxIntersections === n ? "rgba(37,99,235,.2)" : "var(--border)"}`,
                }}
              >
                {n}
              </button>
            ))}
          </div>
        </Row>
      </Section>

      {/* ML */}
      <Section title="Model AI">
        <Row label="ML Mode" sub="Mode inferensi yang aktif">
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "3px 10px",
              borderRadius: 20,
              background: "rgba(124,58,237,.1)",
              color: "var(--purple)",
              border: "1px solid rgba(124,58,237,.2)",
            }}
          >
            {status?.ml_mode ?? "—"}
          </span>
        </Row>
        <Row label="Horizons Prediksi" sub="Jangka waktu prediksi tersedia">
          <span style={{ fontSize: 11, color: "var(--text-dim)" }}>
            {status?.supported_horizons?.join(", ") ?? "—"}
          </span>
        </Row>
        <Row label="ML Fallback" sub="Aktif jika model LSTM belum tersedia">
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "3px 10px",
              borderRadius: 20,
              background: status?.ml_fallback_active
                ? "rgba(251,191,36,.1)"
                : "rgba(74,222,128,.1)",
              color: status?.ml_fallback_active ? "var(--yellow)" : "var(--green)",
              border: `1px solid ${status?.ml_fallback_active ? "rgba(251,191,36,.2)" : "rgba(74,222,128,.2)"}`,
            }}
          >
            {status?.ml_fallback_active ? "Aktif" : "Nonaktif"}
          </span>
        </Row>
        <Row label="Model MAPE" sub="Error prediksi LSTM dari hasil inference">
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: "var(--green)",
              background: "rgba(74,222,128,.1)",
              border: "1px solid rgba(74,222,128,.2)",
              padding: "3px 10px",
              borderRadius: 20,
            }}
          >
            20.60%
          </span>
        </Row>

        <Row
          label="Dataset Inference"
          sub="Total video CCTV yang diproses YOLO"
        >
          <span style={{ fontSize: 11, color: "#94a3b8" }}>21 video</span>
        </Row>

        <Row label="Horizon Didukung" sub="Jangka waktu prediksi LSTM">
          <span style={{ fontSize: 11, color: "var(--purple)" }}>15m · 2h · 4h</span>
        </Row>
      </Section>

      {/* System info */}
      <Section title="Informasi Sistem">
        <Row label="Backend Status" sub="Koneksi ke FastAPI">
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "3px 10px",
              borderRadius: 20,
              background: "rgba(74,222,128,.1)",
              color: "var(--green)",
              border: "1px solid rgba(74,222,128,.2)",
            }}
          >
            Terhubung
          </span>
        </Row>
        <Row label="Dataset" sub="Hybrid traffic dataset Tomang">
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "3px 10px",
              borderRadius: 20,
              background: status?.dataset_ready
                ? "rgba(74,222,128,.1)"
                : "rgba(71,85,105,.1)",
              color: status?.dataset_ready ? "var(--green)" : "var(--text-dim)",
              border: `1px solid ${status?.dataset_ready ? "rgba(74,222,128,.2)" : "rgba(71,85,105,.2)"}`,
            }}
          >
            {status?.dataset_ready ? "Tersedia" : "Tidak tersedia"}
          </span>
        </Row>
        <Row label="Camera Input" sub="YOLO pipeline">
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "3px 10px",
              borderRadius: 20,
              background: status?.camera_ready
                ? "rgba(74,222,128,.1)"
                : "rgba(71,85,105,.1)",
              color: status?.camera_ready ? "var(--green)" : "var(--text-dim)",
              border: `1px solid ${status?.camera_ready ? "rgba(74,222,128,.2)" : "rgba(71,85,105,.2)"}`,
            }}
          >
            {status?.camera_ready ? "Aktif" : "Nonaktif"}
          </span>
        </Row>
        <Row
          label="Fail-safe"
          sub="Auto-switch ke local timer jika API terputus"
        >
          <span
            style={{
              fontSize: 11,
              fontWeight: 600,
              padding: "3px 10px",
              borderRadius: 20,
              background: "rgba(74,222,128,.1)",
              color: "var(--green)",
              border: "1px solid rgba(74,222,128,.2)",
            }}
          >
            Aktif
          </span>
        </Row>
      </Section>
    </div>
  );
};
