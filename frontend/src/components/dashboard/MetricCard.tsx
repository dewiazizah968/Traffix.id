interface Props {
  label: string;
  value: string | number;
  sub?: string;
  icon: string;
  accent: "blue" | "green" | "orange" | "purple";
}

const cfg = {
  blue: {
    glow: "var(--blue-bg)",
    text: "var(--blue)",
    dim: "var(--blue-bg)",
  },
  green: {
    glow: "var(--green-bg)",
    text: "var(--green)",
    dim: "var(--green-bg)",
  },
  orange: {
    glow: "var(--orange-bg)",
    text: "var(--orange)",
    dim: "var(--orange-bg)",
  },
  purple: {
    glow: "var(--purple-bg)",
    text: "var(--purple)",
    dim: "var(--purple-bg)",
  },
};

export const MetricCard = ({ label, value, sub, icon, accent }: Props) => {
  const c = cfg[accent];
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: 10,
        padding: "12px 14px",
        position: "relative",
        overflow: "hidden",
        animation: "fadeIn .3s ease",
        transition: "background .3s, border-color .3s",
      }}
    >
      {/* Glow bg */}
      <div
        style={{
          position: "absolute",
          top: -10,
          right: -10,
          width: 60,
          height: 60,
          borderRadius: "50%",
          background: c.glow,
          filter: "blur(20px)",
          pointerEvents: "none",
        }}
      />

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <div
          style={{
            width: 28,
            height: 28,
            borderRadius: 7,
            background: c.dim,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 13,
            flexShrink: 0,
          }}
        >
          {icon}
        </div>
        <p
          style={{
            fontSize: 10,
            color: "var(--text-muted)",
            textTransform: "uppercase",
            letterSpacing: ".08em",
          }}
        >
          {label}
        </p>
      </div>

      <p
        style={{
          fontSize: 20,
          fontWeight: 700,
          color: "var(--text-primary)",
          letterSpacing: "-.5px",
          lineHeight: 1,
        }}
      >
        {value}
      </p>
      {sub && (
        <p style={{ fontSize: 11, color: c.text, marginTop: 4 }}>{sub}</p>
      )}
    </div>
  );
};
