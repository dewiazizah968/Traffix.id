import { useState, type FormEvent } from "react";
import { useAuth } from "../lib/AuthContext";

export const LoginPage = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Username dan password harus diisi");
      return;
    }
    setLoading(true);
    setError(null);
    // Simulate network delay
    setTimeout(() => {
      const err = login(username, password);
      if (err) setError(err);
      setLoading(false);
    }, 600);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #060b18 0%, #0c1a3a 40%, #162050 70%, #0a1228 100%)",
        position: "relative",
        overflow: "hidden",
        fontFamily: "'Inter', 'Segoe UI', sans-serif",
      }}
    >
      {/* Animated background orbs */}
      <div
        style={{
          position: "absolute",
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(59,130,246,.12) 0%, transparent 70%)",
          top: "-10%",
          right: "-5%",
          animation: "float 8s ease-in-out infinite",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 400,
          height: 400,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(52,211,153,.08) 0%, transparent 70%)",
          bottom: "-8%",
          left: "-3%",
          animation: "float 10s ease-in-out infinite reverse",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 250,
          height: 250,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(167,139,250,.1) 0%, transparent 70%)",
          top: "40%",
          left: "20%",
          animation: "float 12s ease-in-out infinite",
        }}
      />

      {/* Grid lines */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(59,130,246,.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,.04) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }}
      />

      {/* Login card */}
      <div
        style={{
          position: "relative",
          zIndex: 1,
          width: 400,
          background: "rgba(12,21,37,.85)",
          backdropFilter: "blur(24px)",
          border: "1px solid rgba(59,130,246,.15)",
          borderRadius: 20,
          padding: "36px 32px 32px",
          boxShadow:
            "0 30px 80px rgba(0,0,0,.6), 0 0 0 1px rgba(59,130,246,.08) inset, 0 0 60px rgba(59,130,246,.05)",
          animation: "fadeIn .5s ease",
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              background: "linear-gradient(135deg, #3b82f6, #2563eb)",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: 14,
              boxShadow: "0 8px 24px rgba(37,99,235,.35)",
            }}
          >
            <span style={{ fontSize: 24 }}>🚦</span>
          </div>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: "#f0f4ff",
              margin: 0,
              letterSpacing: "-.3px",
            }}
          >
            Traffix<span style={{ color: "#3b82f6" }}>.id</span>
          </h1>
          <p
            style={{
              fontSize: 13,
              color: "#6b7fa8",
              marginTop: 6,
            }}
          >
            AI-Powered Traffic Management System
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {/* Username */}
          <div style={{ marginBottom: 14 }}>
            <label
              style={{
                display: "block",
                fontSize: 11,
                fontWeight: 500,
                color: "#8899b8",
                marginBottom: 6,
                textTransform: "uppercase",
                letterSpacing: ".06em",
              }}
            >
              Username
            </label>
            <div style={{ position: "relative" }}>
              <span
                style={{
                  position: "absolute",
                  left: 12,
                  top: "50%",
                  transform: "translateY(-50%)",
                  fontSize: 14,
                  color: "#5c6e8a",
                }}
              >
                👤
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Masukkan username"
                autoComplete="username"
                style={{
                  width: "100%",
                  padding: "11px 14px 11px 36px",
                  fontSize: 13,
                  color: "#e0e8f5",
                  background: "rgba(6,11,24,.7)",
                  border: "1px solid rgba(26,39,68,.9)",
                  borderRadius: 10,
                  outline: "none",
                  transition: "border-color .2s, box-shadow .2s",
                  boxSizing: "border-box",
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = "rgba(59,130,246,.5)";
                  e.target.style.boxShadow = "0 0 0 3px rgba(59,130,246,.1)";
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = "rgba(26,39,68,.9)";
                  e.target.style.boxShadow = "none";
                }}
              />
            </div>
          </div>

          {/* Password */}
          <div style={{ marginBottom: 18 }}>
            <label
              style={{
                display: "block",
                fontSize: 11,
                fontWeight: 500,
                color: "#8899b8",
                marginBottom: 6,
                textTransform: "uppercase",
                letterSpacing: ".06em",
              }}
            >
              Password
            </label>
            <div style={{ position: "relative" }}>
              <span
                style={{
                  position: "absolute",
                  left: 12,
                  top: "50%",
                  transform: "translateY(-50%)",
                  fontSize: 14,
                  color: "#5c6e8a",
                }}
              >
                🔒
              </span>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan password"
                autoComplete="current-password"
                style={{
                  width: "100%",
                  padding: "11px 40px 11px 36px",
                  fontSize: 13,
                  color: "#e0e8f5",
                  background: "rgba(6,11,24,.7)",
                  border: "1px solid rgba(26,39,68,.9)",
                  borderRadius: 10,
                  outline: "none",
                  transition: "border-color .2s, box-shadow .2s",
                  boxSizing: "border-box",
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = "rgba(59,130,246,.5)";
                  e.target.style.boxShadow = "0 0 0 3px rgba(59,130,246,.1)";
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = "rgba(26,39,68,.9)";
                  e.target.style.boxShadow = "none";
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: "absolute",
                  right: 10,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: "#5c6e8a",
                  fontSize: 13,
                  cursor: "pointer",
                  padding: 2,
                }}
              >
                {showPassword ? "🙈" : "👁"}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div
              style={{
                marginBottom: 14,
                padding: "8px 12px",
                borderRadius: 8,
                background: "rgba(251,113,133,.08)",
                border: "1px solid rgba(251,113,133,.2)",
                color: "#fb7185",
                fontSize: 12,
                display: "flex",
                alignItems: "center",
                gap: 6,
                animation: "fadeIn .2s ease",
              }}
            >
              <span>⚠️</span> {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px 0",
              fontSize: 14,
              fontWeight: 600,
              color: "#fff",
              background: loading
                ? "linear-gradient(135deg, #2050a0, #1a3f80)"
                : "linear-gradient(135deg, #3b82f6, #2563eb)",
              border: "none",
              borderRadius: 10,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "all .2s",
              boxShadow: "0 6px 20px rgba(37,99,235,.3)",
              position: "relative",
              overflow: "hidden",
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                (e.target as HTMLButtonElement).style.boxShadow =
                  "0 8px 28px rgba(37,99,235,.45)";
                (e.target as HTMLButtonElement).style.transform = "translateY(-1px)";
              }
            }}
            onMouseLeave={(e) => {
              (e.target as HTMLButtonElement).style.boxShadow =
                "0 6px 20px rgba(37,99,235,.3)";
              (e.target as HTMLButtonElement).style.transform = "translateY(0)";
            }}
          >
            {loading ? (
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <span
                  style={{
                    width: 16,
                    height: 16,
                    border: "2px solid rgba(255,255,255,.3)",
                    borderTopColor: "#fff",
                    borderRadius: "50%",
                    display: "inline-block",
                    animation: "spin .6s linear infinite",
                  }}
                />
                Signing in...
              </span>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        {/* Demo hint */}
        <div
          style={{
            background: "rgba(6,11,24,.5)",
            border: "1px solid rgba(26,39,68,.8)",
            borderRadius: 8,
            padding: "10px 14px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <p style={{ fontSize: 10, color: "#4a5a78", marginBottom: 3 }}>DEMO CREDENTIAL</p>
            <p style={{ fontSize: 12, color: "#8899b8" }}>
              <span style={{ color: "#e0e8f5" }}>admin</span> / <span style={{ color: "#e0e8f5" }}>admin123</span>
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setUsername("admin");
              setPassword("admin123");
              setError(null);
            }}
            style={{
              padding: "6px 14px",
              fontSize: 11,
              fontWeight: 500,
              color: "#3b82f6",
              background: "rgba(59,130,246,.1)",
              border: "1px solid rgba(59,130,246,.2)",
              borderRadius: 6,
              cursor: "pointer",
              transition: "all .15s",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "rgba(59,130,246,.2)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = "rgba(59,130,246,.1)";
            }}
          >
            Auto Fill
          </button>
        </div>

        {/* Footer */}
        <p
          style={{
            textAlign: "center",
            fontSize: 10,
            color: "#3d5070",
            marginTop: 20,
          }}
        >
          © 2026 Traffix.id · AI-Powered Traffic System
        </p>
      </div>

      {/* CSS animations */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-20px); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};
