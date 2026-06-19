import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { usePredictions } from "../../hooks/useTraffixData";

interface Props {
  intersectionId: string;
  currentCount?: number;
}

const sourceStyle = {
  lstm: {
    color: "var(--green)",
    bg: "var(--green-bg)",
    border: "var(--green-border)",
    label: "LSTM ✓",
  },
  dataset: {
    color: "var(--yellow)",
    bg: "var(--yellow-bg)",
    border: "var(--yellow-border)",
    label: "Dataset",
  },
  heuristic: {
    color: "var(--blue)",
    bg: "var(--blue-bg)",
    border: "var(--blue-border)",
    label: "Heuristik",
  },
};

const congestionColor = (level: string) => {
  if (level === "Critical") return "var(--red)";
  if (level === "High") return "var(--orange)";
  if (level === "Medium") return "var(--yellow)";
  return "var(--green)";
};

// Bulatkan ke 15 menit terdekat
const roundToNearest15 = (date: Date): Date => {
  const ms = 15 * 60 * 1000;
  return new Date(Math.round(date.getTime() / ms) * ms);
};

const getTimeLabel = (horizon: string): string => {
  const now = new Date();
  const clone = new Date(now);

  if (horizon === "15m") clone.setMinutes(clone.getMinutes() + 15);
  else if (horizon === "2h") clone.setHours(clone.getHours() + 2);
  else if (horizon === "4h") clone.setHours(clone.getHours() + 4);
  else return horizon;

  const rounded = roundToNearest15(clone);
  return rounded.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

const getNowLabel = (): string => {
  const rounded = roundToNearest15(new Date());
  return rounded.toLocaleTimeString("id-ID", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

export const PredictionChart = ({ intersectionId, currentCount }: Props) => {
  const { data, isLoading, isError } = usePredictions(intersectionId);

  if (isLoading)
    return (
      <div
        style={{
          height: 180,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg-elevated)",
          borderRadius: 10,
        }}
      >
        <p
          style={{
            fontSize: 12,
            color: "#7b8fa3",
            animation: "pulse 1.5s infinite",
          }}
        >
          Loading prediksi...
        </p>
      </div>
    );

  if (isError || !data?.predictions?.length)
    return (
      <div
        style={{
          height: 180,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "var(--bg-elevated)",
          borderRadius: 10,
        }}
      >
        <p style={{ fontSize: 11, color: "var(--red)" }}>
          Tidak ada data prediksi
        </p>
      </div>
    );

  const mlMode = data.predictions[0]?.source ?? "heuristic";
  const ss =
    sourceStyle[mlMode as keyof typeof sourceStyle] ?? sourceStyle.heuristic;
  const isDataset = mlMode === "dataset";
  const isLSTM = mlMode === "lstm" || mlMode.startsWith("lstm");

  // Jika LSTM memprediksi volume per jam, skalakan jumlah kendaraan 1-menit saat ini agar seimbang di grafik
  const chartCurrentCount = isLSTM && currentCount != null ? currentCount * 60 : currentCount;

  const chartData = [
    // Titik sekarang
    ...(currentCount != null && chartCurrentCount != null
      ? [
          {
            horizon: getNowLabel(),
            nilai: chartCurrentCount,
            level: "Now",
            source: "live",
            confidence: 100,
            rawCount: currentCount,
            isNow: true,
          },
        ]
      : []),
    // Titik prediksi
    ...data.predictions.map((p) => ({
      horizon: getTimeLabel(p.horizon),
      nilai:
        isDataset && chartCurrentCount && chartCurrentCount > 0
          ? Math.round(
              ((p.predicted_vehicle_count - chartCurrentCount) / chartCurrentCount) * 100,
            )
          : p.predicted_vehicle_count,
      level: p.predicted_congestion_level,
      source: p.source,
      confidence: Math.round(p.confidence_score * 100),
      rawCount: p.predicted_vehicle_count,
      isNow: false,
    })),
  ];

  // Domain Y
  const vals = chartData.map((d) => d.nilai);
  const pad = (Math.max(...vals) - Math.min(...vals)) * 0.25 || 20;
  const yMin = Math.max(
    isDataset ? -100 : 0,
    Math.floor(Math.min(...vals) - pad),
  );
  const yMax = Math.ceil(Math.max(...vals) + pad);

  const Tip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-hover)",
          borderRadius: 8,
          padding: "10px 13px",
          fontSize: 12,
        }}
      >
        <p style={{ color: "var(--text-muted)", marginBottom: 5, fontWeight: 500 }}>
          {d.isNow ? `Sekarang · ${label}` : `${label} WIB`}
        </p>

        {isDataset && !d.isNow ? (
          <>
            <p
              style={{
                fontWeight: 600,
                fontSize: 14,
                color: d.nilai > 0 ? "var(--red)" : "var(--green)",
              }}
            >
              {d.nilai > 0 ? "▲" : "▼"} {Math.abs(d.nilai)}% dari sekarang
            </p>
            <p style={{ color: "#7b8fa3", marginTop: 3, fontSize: 11 }}>
              Volume: {d.rawCount.toLocaleString()} kend/jam
            </p>
          </>
        ) : (
          <p
            style={{
              fontWeight: 600,
              fontSize: 14,
              color: d.isNow ? "var(--green)" : "#2563eb",
            }}
          >
            {d.nilai.toLocaleString()} {isLSTM ? "kend/jam" : "kendaraan"}
          </p>
        )}

        {!d.isNow && (
          <>
            <p style={{ color: congestionColor(d.level), marginTop: 3 }}>
              {d.level}
              {d.confidence > 0 && ` · ${d.confidence}% yakin`}
            </p>
            <p style={{ color: ss.color, marginTop: 2, fontSize: 11 }}>
              Sumber: {d.source}
            </p>
          </>
        )}

        {chartCurrentCount != null && !d.isNow && !isDataset && (
          <p
            style={{
              marginTop: 4,
              fontSize: 11,
              color: d.nilai > chartCurrentCount ? "var(--red)" : "var(--green)",
            }}
          >
            {d.nilai > chartCurrentCount ? "▲" : "▼"}{" "}
            {Math.abs(d.nilai - chartCurrentCount).toLocaleString()} dari estimasi saat ini
          </p>
        )}
      </div>
    );
  };

  return (
    <div style={{ background: "var(--bg-elevated)", borderRadius: 10, padding: 12 }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: "var(--green)",
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: 12, color: "#7b8fa3" }}>Sekarang</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span
              style={{
                width: 14,
                height: 2,
                background: "#2563eb",
                display: "inline-block",
                borderRadius: 2,
              }}
            />
            <span style={{ fontSize: 12, color: "#7b8fa3" }}>
              {isDataset ? "% Perubahan" : "Prediksi"}
            </span>
          </div>
        </div>
        <span
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: ss.color,
            background: ss.bg,
            border: `1px solid ${ss.border}`,
            padding: "1px 8px",
            borderRadius: 20,
          }}
        >
          {ss.label}
        </span>
      </div>

      {/* Congestion cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3,1fr)",
          gap: 6,
          marginBottom: 10,
        }}
      >
        {data.predictions.map((p) => (
          <div
            key={p.horizon}
            style={{
              background: "var(--bg-card)",
              borderRadius: 7,
              padding: "7px 8px",
              border: `1px solid ${congestionColor(p.predicted_congestion_level)}22`,
              textAlign: "center",
            }}
          >
            <p style={{ fontSize: 11, color: "#7b8fa3", marginBottom: 1 }}>
              +{p.horizon}
            </p>
            <p
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "#b0bec5",
                marginBottom: 3,
              }}
            >
              {getTimeLabel(p.horizon)} WIB
            </p>
            <p
              style={{
                fontSize: 15,
                fontWeight: 600,
                color: congestionColor(p.predicted_congestion_level),
              }}
            >
              {p.predicted_congestion_level}
            </p>
            {p.confidence_score > 0 && (
              <p style={{ fontSize: 11, color: "#7b8fa3", marginTop: 2 }}>
                {Math.round(p.confidence_score * 100)}% yakin
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Line chart */}
      <ResponsiveContainer width="100%" height={140}>
        <LineChart
          data={chartData}
          margin={{ top: 4, right: 4, bottom: 0, left: -16 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="horizon" tick={{ fill: "var(--text-dim)", fontSize: 10 }} />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fill: "var(--text-dim)", fontSize: 10 }}
            tickFormatter={(v) =>
              isDataset
                ? `${v}%`
                : v >= 1000
                  ? `${(v / 1000).toFixed(1)}k`
                  : String(v)
            }
          />
          <Tooltip content={<Tip />} />

          {/* Garis referensi 0 untuk dataset mode */}
          {isDataset && (
            <ReferenceLine y={0} stroke="#334155" strokeDasharray="4 3" />
          )}

          {/* Garis referensi nilai sekarang */}
          {chartCurrentCount != null && !isDataset && (
            <ReferenceLine
              y={chartCurrentCount}
              stroke="var(--green)"
              strokeDasharray="4 3"
              strokeOpacity={0.4}
            />
          )}

          <Line
            type="monotone"
            dataKey="nilai"
            stroke="#2563eb"
            strokeWidth={2}
            dot={(props: any) => {
              const { cx, cy, payload } = props;
              return (
                <circle
                  key={`dot-${payload.horizon}`}
                  cx={cx}
                  cy={cy}
                  r={payload.isNow ? 5 : 4}
                  fill={payload.isNow ? "var(--green)" : "#2563eb"}
                  stroke="var(--bg-elevated)"
                  strokeWidth={2}
                />
              );
            }}
            activeDot={{
              r: 6,
              fill: "#2563eb",
              stroke: "var(--bg-elevated)",
              strokeWidth: 2,
            }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Note dataset mode */}
      {isDataset && (
        <p
          style={{
            fontSize: 9,
            color: "var(--text-dim)",
            marginTop: 8,
            lineHeight: 1.5,
          }}
        >
          ⚠️ Mode dataset — ditampilkan sebagai % perubahan relatif terhadap
          kondisi live saat ini.
        </p>
      )}
    </div>
  );
};
