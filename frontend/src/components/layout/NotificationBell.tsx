import { useState } from "react";
import { useNotifications } from "../../hooks/useTraffixData";

export const NotificationBell = () => {
  const [open, setOpen] = useState(false);
  const { notifications, markAllRead, unreadCount } = useNotifications();

  const typeConfig = {
    critical: {
      icon: "🔴",
      color: "var(--red)",
      bg: "rgba(248,113,113,.08)",
      border: "rgba(248,113,113,.15)",
    },
    warning: {
      icon: "⚠️",
      color: "var(--yellow)",
      bg: "rgba(251,191,36,.08)",
      border: "rgba(251,191,36,.15)",
    },
    success: {
      icon: "✅",
      color: "var(--green)",
      bg: "rgba(74,222,128,.08)",
      border: "rgba(74,222,128,.15)",
    },
    info: {
      icon: "ℹ️",
      color: "var(--blue)",
      bg: "rgba(96,165,250,.08)",
      border: "rgba(96,165,250,.15)",
    },
  };

  const timeAgo = (ts: string) => {
    const diff = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
    if (diff < 60) return `${diff} detik lalu`;
    if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`;
    return `${Math.floor(diff / 3600)} jam lalu`;
  };

  return (
    <div style={{ position: "relative" }}>
      <button
        onClick={() => {
          setOpen(!open);
          if (!open) markAllRead();
        }}
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          border: "1px solid #161d27",
          background: open ? "var(--border)" : "transparent",
          color: "var(--text-dim)",
          fontSize: 15,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          transition: "background .15s",
        }}
      >
        🔔
        {unreadCount > 0 && (
          <span
            style={{
              position: "absolute",
              top: -3,
              right: -3,
              width: 16,
              height: 16,
              borderRadius: "50%",
              background: "var(--red)",
              color: "#fff",
              fontSize: 9,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              border: "2px solid #0d1117",
            }}
          >
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div
            onClick={() => setOpen(false)}
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 98,
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 38,
              right: 0,
              width: 320,
              maxHeight: 400,
              overflowY: "auto",
              background: "var(--bg-card)",
              border: "1px solid #1e2736",
              borderRadius: 12,
              zIndex: 99,
              boxShadow: "0 20px 60px rgba(0,0,0,.6)",
              animation: "fadeIn .15s ease",
            }}
          >
            <div
              style={{
                padding: "12px 14px",
                borderBottom: "1px solid #161d27",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <p style={{ fontSize: 12, fontWeight: 500, color: "var(--stat-value)" }}>
                Notifikasi
              </p>
              <button
                onClick={markAllRead}
                style={{
                  fontSize: 10,
                  color: "var(--text-dim)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Tandai semua dibaca
              </button>
            </div>

            {notifications.length === 0 ? (
              <div style={{ padding: 24, textAlign: "center" }}>
                <p style={{ fontSize: 20, marginBottom: 6 }}>🔕</p>
                <p style={{ fontSize: 12, color: "var(--text-dim)" }}>
                  Tidak ada notifikasi
                </p>
              </div>
            ) : (
              notifications.map((n) => {
                const c = typeConfig[n.type];
                return (
                  <div
                    key={n.id}
                    style={{
                      padding: "10px 14px",
                      borderBottom: "1px solid #161d27",
                      background: n.read
                        ? "transparent"
                        : "rgba(255,255,255,.02)",
                      display: "flex",
                      gap: 10,
                      alignItems: "flex-start",
                    }}
                  >
                    <div
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: 8,
                        flexShrink: 0,
                        background: c.bg,
                        border: `1px solid ${c.border}`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 13,
                      }}
                    >
                      {c.icon}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p
                        style={{
                          fontSize: 12,
                          color: n.read ? "var(--text-dim)" : "var(--text-secondary)",
                          lineHeight: 1.4,
                          marginBottom: 2,
                        }}
                      >
                        {n.message}
                      </p>
                      <p style={{ fontSize: 10, color: "var(--text-dim)" }}>
                        {timeAgo(n.timestamp)}
                      </p>
                    </div>
                    {!n.read && (
                      <span
                        style={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          background: c.color,
                          flexShrink: 0,
                          marginTop: 4,
                        }}
                      />
                    )}
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
};
