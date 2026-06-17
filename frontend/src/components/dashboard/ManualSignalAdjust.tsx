import { useState, useEffect } from "react";
import type { Intersection } from "../../types";
import {
  useManualOverride,
  useClearManualOverride,
} from "../../hooks/useTraffixData";

interface Props {
  intersection: Intersection;
}

export const ManualSignalAdjust = ({ intersection }: Props) => {
  const [value, setValue] = useState(intersection.green_duration_seconds);
  const [manualMode, setManualMode] = useState(false);
  const [overrideDuration, setOverrideDuration] = useState(5); // minutes

  const overrideMutation = useManualOverride();
  const clearMutation = useClearManualOverride();

  // Sync slider value with live data when NOT in manual mode
  useEffect(() => {
    if (!manualMode) {
      setValue(intersection.green_duration_seconds);
    }
  }, [intersection.green_duration_seconds, manualMode]);

  const handleApply = () => {
    overrideMutation.mutate({
      intersectionId: intersection.intersection_id,
      greenDurationSeconds: value,
      durationMinutes: overrideDuration,
    });
  };

  const handleReset = () => {
    clearMutation.mutate(intersection.intersection_id);
    setValue(intersection.green_duration_seconds);
    setManualMode(false);
  };

  const isPending = overrideMutation.isPending || clearMutation.isPending;
  const isSuccess = overrideMutation.isSuccess;
  const isError = overrideMutation.isError;

  return (
    <div
      style={{
        background: "var(--bg-elevated)",
        border: "1px solid #161d27",
        borderRadius: 10,
        padding: 14,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <p
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "var(--text-secondary)",
            display: "flex",
            alignItems: "center",
            gap: 5,
          }}
        >
          🚦 Pengaturan Sinyal Manual
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {manualMode && (
            <span
              style={{
                fontSize: 9,
                fontWeight: 600,
                padding: "2px 7px",
                borderRadius: 20,
                background: "rgba(251,191,36,.1)",
                color: "var(--yellow)",
                border: "1px solid rgba(251,191,36,.2)",
                animation: "pulse 2s infinite",
              }}
            >
              MANUAL
            </span>
          )}
          <button
            onClick={() => {
              if (manualMode) {
                handleReset();
              } else {
                setManualMode(true);
              }
            }}
            disabled={isPending}
            style={{
              fontSize: 10,
              padding: "3px 10px",
              borderRadius: 6,
              cursor: isPending ? "wait" : "pointer",
              background: manualMode
                ? "rgba(248,113,113,.08)"
                : "rgba(37,99,235,.08)",
              color: manualMode ? "var(--red)" : "var(--blue)",
              border: `1px solid ${manualMode ? "rgba(248,113,113,.2)" : "rgba(37,99,235,.2)"}`,
              opacity: isPending ? 0.6 : 1,
            }}
          >
            {isPending ? "..." : manualMode ? "Nonaktifkan" : "Aktifkan"}
          </button>
        </div>
      </div>

      {manualMode && (
        <>
          {/* Current vs Manual */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 8,
              marginBottom: 12,
            }}
          >
            <div
              style={{ background: "var(--bg-card)", borderRadius: 8, padding: 10 }}
            >
              <p style={{ fontSize: 9, color: "var(--text-dim)", marginBottom: 3 }}>
                Durasi Saat Ini
              </p>
              <p style={{ fontSize: 18, fontWeight: 600, color: "var(--text-secondary)" }}>
                {intersection.green_duration_seconds}
                <span style={{ fontSize: 11, color: "var(--text-dim)" }}>s</span>
              </p>
            </div>
            <div
              style={{ background: "var(--bg-card)", borderRadius: 8, padding: 10 }}
            >
              <p style={{ fontSize: 9, color: "var(--text-dim)", marginBottom: 3 }}>
                Durasi Baru
              </p>
              <p
                style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color:
                    value !== intersection.green_duration_seconds
                      ? "var(--yellow)"
                      : "var(--text-secondary)",
                }}
              >
                {value}
                <span style={{ fontSize: 11, color: "var(--text-dim)" }}>s</span>
              </p>
            </div>
          </div>

          {/* Slider */}
          <div style={{ marginBottom: 10 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: 10,
                color: "var(--text-dim)",
                marginBottom: 6,
              }}
            >
              <span>15s (minimum)</span>
              <span style={{ color: "var(--text-secondary)", fontWeight: 500 }}>
                {value}s
              </span>
              <span>120s (maksimum)</span>
            </div>
            <input
              type="range"
              min={15}
              max={120}
              value={value}
              onChange={(e) => setValue(Number(e.target.value))}
              style={{
                width: "100%",
                accentColor: "var(--yellow)",
                cursor: "pointer",
              }}
            />
          </div>

          {/* Quick presets */}
          <div style={{ display: "flex", gap: 6, marginBottom: 12 }}>
            {[30, 45, 60, 90].map((preset) => (
              <button
                key={preset}
                onClick={() => setValue(preset)}
                style={{
                  flex: 1,
                  padding: "5px 0",
                  fontSize: 11,
                  borderRadius: 6,
                  cursor: "pointer",
                  background:
                    value === preset ? "rgba(251,191,36,.1)" : "var(--bg-card)",
                  color: value === preset ? "var(--yellow)" : "var(--text-dim)",
                  border: `1px solid ${value === preset ? "rgba(251,191,36,.2)" : "var(--border)"}`,
                  transition: "all .15s",
                }}
              >
                {preset}s
              </button>
            ))}
          </div>

          {/* Override duration selector */}
          <div style={{ marginBottom: 12 }}>
            <p
              style={{
                fontSize: 9,
                color: "var(--text-dim)",
                marginBottom: 6,
                textTransform: "uppercase",
                letterSpacing: ".05em",
              }}
            >
              Durasi Override Aktif
            </p>
            <div style={{ display: "flex", gap: 6 }}>
              {[1, 5, 15, 30].map((mins) => (
                <button
                  key={mins}
                  onClick={() => setOverrideDuration(mins)}
                  style={{
                    flex: 1,
                    padding: "4px 0",
                    fontSize: 10,
                    borderRadius: 6,
                    cursor: "pointer",
                    background:
                      overrideDuration === mins
                        ? "rgba(96,165,250,.1)"
                        : "var(--bg-card)",
                    color:
                      overrideDuration === mins ? "var(--blue)" : "var(--text-dim)",
                    border: `1px solid ${overrideDuration === mins ? "rgba(96,165,250,.2)" : "var(--border)"}`,
                    transition: "all .15s",
                  }}
                >
                  {mins} mnt
                </button>
              ))}
            </div>
          </div>

          {/* Status feedback */}
          {isSuccess && (
            <div
              style={{
                marginBottom: 10,
                padding: "6px 10px",
                borderRadius: 6,
                background: "rgba(74,222,128,.06)",
                border: "1px solid rgba(74,222,128,.15)",
                fontSize: 10,
                color: "var(--green)",
                textAlign: "center",
              }}
            >
              ✓ Override berhasil diterapkan — durasi hijau: {value}s selama{" "}
              {overrideDuration} menit
            </div>
          )}
          {isError && (
            <div
              style={{
                marginBottom: 10,
                padding: "6px 10px",
                borderRadius: 6,
                background: "rgba(248,113,113,.06)",
                border: "1px solid rgba(248,113,113,.15)",
                fontSize: 10,
                color: "var(--red)",
                textAlign: "center",
              }}
            >
              ✗ Gagal menerapkan override — periksa koneksi backend
            </div>
          )}

          {/* Actions */}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleApply}
              disabled={isPending}
              style={{
                flex: 2,
                padding: "8px 0",
                fontSize: 11,
                fontWeight: 600,
                borderRadius: 7,
                cursor: isPending ? "wait" : "pointer",
                background: isSuccess
                  ? "rgba(74,222,128,.08)"
                  : "rgba(251,191,36,.08)",
                color: isSuccess ? "var(--green)" : "var(--yellow)",
                border: `1px solid ${isSuccess ? "rgba(74,222,128,.2)" : "rgba(251,191,36,.2)"}`,
                transition: "all .3s",
                opacity: isPending ? 0.6 : 1,
              }}
            >
              {isPending
                ? "Menerapkan..."
                : isSuccess
                  ? "✓ Diterapkan"
                  : "Terapkan ke Server"}
            </button>
            <button
              onClick={handleReset}
              disabled={isPending}
              style={{
                flex: 1,
                padding: "8px 0",
                fontSize: 11,
                fontWeight: 600,
                borderRadius: 7,
                cursor: isPending ? "wait" : "pointer",
                background: "transparent",
                color: "var(--text-dim)",
                border: "1px solid #161d27",
                opacity: isPending ? 0.6 : 1,
              }}
            >
              Reset
            </button>
          </div>
        </>
      )}
    </div>
  );
};
