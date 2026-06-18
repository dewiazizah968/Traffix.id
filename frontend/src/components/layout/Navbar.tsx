import { useSystemStatus } from "../../hooks/useTraffixData";
import { NotificationBell } from "./NotificationBell";
import { useTheme } from "../../lib/ThemeContext";
import { useAuth } from "../../lib/AuthContext";

interface Props {
  page: string;
  onNavigate: (p: string) => void;
}

export const Navbar = ({ page, onNavigate }: Props) => {
  const { data: status } = useSystemStatus();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const isDark = theme === "dark";

  return (
    <nav
      style={{
        display: "flex",
        alignItems: "center",
        height: 48,
        padding: "0 20px",
        background: "var(--bg-card)",
        borderBottom: "1px solid var(--border)",
        flexShrink: 0,
        transition: "background .3s, border-color .3s",
      }}
    >
      {/* Logo */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginRight: 32,
        }}
      >
        <div
          style={{
            width: 26,
            height: 26,
            borderRadius: 7,
            background: "linear-gradient(135deg, #2563eb, #0ea5e9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 13,
            boxShadow: "0 0 12px rgba(37,99,235,0.4)",
          }}
        >
          <img
            src="/logo.png"
            alt="Traffix.id"
            style={{
              width: 26,
              height: 26,
              borderRadius: 7,
              objectFit: "contain",
            }}
          />
        </div>
        <span
          style={{
            fontSize: 14,
            fontWeight: 600,
            color: "var(--text-primary)",
            letterSpacing: "-.3px",
            transition: "color .3s",
          }}
        >
          Traffix<span style={{ color: "#2563eb" }}>.id</span>
        </span>
      </div>

      {/* Tabs */}
      {[
        { id: "dashboard", label: "Dashboard" },
        { id: "map", label: "Live Map" },
        { id: "settings", label: "Settings" },
      ].map((tab) => (
        <button
          key={tab.id}
          onClick={() => onNavigate(tab.id)}
          style={{
            height: 48,
            padding: "0 14px",
            background: "none",
            border: "none",
            borderBottom: `2px solid ${page === tab.id ? "#2563eb" : "transparent"}`,
            color: page === tab.id ? "var(--text-primary)" : "var(--text-muted)",
            fontSize: 12,
            fontWeight: 500,
            cursor: "pointer",
            transition: "color .15s",
          }}
        >
          {tab.label}
        </button>
      ))}

      <div
        style={{
          marginLeft: "auto",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        {/* Status pill */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            padding: "4px 10px",
            borderRadius: 20,
            fontSize: 11,
            background: status?.simulation_active
              ? "rgba(22,163,74,.12)"
              : isDark ? "rgba(71,85,105,.1)" : "rgba(71,85,105,.06)",
            border: `1px solid ${status?.simulation_active ? "rgba(22,163,74,.2)" : "var(--border)"}`,
            color: status?.simulation_active ? "var(--green)" : "var(--text-muted)",
            transition: "all .3s",
          }}
        >
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              display: "inline-block",
              background: status?.simulation_active ? "var(--green)" : "var(--text-dim)",
              animation: status?.simulation_active
                ? "pulse 2s infinite"
                : "none",
            }}
          />
          {status?.simulation_active ? "Operational" : "Idle"}
        </div>

        <NotificationBell />

        {/* ── Theme Toggle Switch ── */}
        <button
          onClick={toggleTheme}
          aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
          style={{
            position: "relative",
            width: 44,
            height: 24,
            borderRadius: 12,
            border: `1px solid ${isDark ? "var(--text-dim)" : "#c0c8d0"}`,
            background: isDark
              ? "linear-gradient(135deg, #1e293b, #0f172a)"
              : "linear-gradient(135deg, #bfdbfe, #93c5fd)",
            cursor: "pointer",
            padding: 0,
            overflow: "hidden",
            transition: "all .3s ease",
            flexShrink: 0,
          }}
        >
          {/* Track decoration — stars (dark) or clouds (light) */}
          {isDark && (
            <>
              <span style={{ position: "absolute", top: 4, left: 6, fontSize: 4, color: "#fde68a", opacity: .7 }}>✦</span>
              <span style={{ position: "absolute", top: 12, left: 10, fontSize: 3, color: "#fde68a", opacity: .5 }}>✦</span>
              <span style={{ position: "absolute", top: 6, left: 15, fontSize: 3, color: "#fde68a", opacity: .4 }}>✦</span>
            </>
          )}
          {!isDark && (
            <>
              <span style={{ position: "absolute", top: 4, right: 8, fontSize: 5, color: "#fff", opacity: .6 }}>☁</span>
              <span style={{ position: "absolute", top: 10, right: 14, fontSize: 4, color: "#fff", opacity: .4 }}>☁</span>
            </>
          )}
          {/* Knob */}
          <span
            style={{
              position: "absolute",
              top: 2,
              left: isDark ? 2 : 22,
              width: 18,
              height: 18,
              borderRadius: "50%",
              background: isDark
                ? "linear-gradient(135deg, #e2e8f0, #cbd5e1)"
                : "linear-gradient(135deg, #fbbf24, #f59e0b)",
              boxShadow: isDark
                ? "inset -2px -1px 0 #94a3b8"
                : "0 0 8px rgba(251,191,36,.5)",
              transition: "left .3s cubic-bezier(.4,0,.2,1), background .3s, box-shadow .3s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 10,
            }}
          >
            {isDark ? "🌙" : "☀️"}
          </span>
        </button>

        {/* Avatar + Logout */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              background: "linear-gradient(135deg,#4f46e5,#7c3aed)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 10,
              fontWeight: 700,
              color: "#fff",
            }}
          >
            {user?.avatar ?? "AT"}
          </div>
          <button
            onClick={logout}
            title="Logout"
            style={{
              background: "none",
              border: "1px solid var(--border)",
              borderRadius: 6,
              color: "var(--text-muted)",
              fontSize: 11,
              padding: "4px 8px",
              cursor: "pointer",
              transition: "all .15s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--red)";
              (e.currentTarget as HTMLButtonElement).style.color = "var(--red)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)";
              (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};
