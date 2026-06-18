import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

export type ThemeMode = "dark" | "light";

interface ThemeContextType {
  theme: ThemeMode;
  toggleTheme: () => void;
  t: (dark: string, light: string) => string;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "dark",
  toggleTheme: () => {},
  t: (dark) => dark,
});

export const useTheme = () => useContext(ThemeContext);

/* ── Token maps ── */
const tokens = {
  dark: {
    // Backgrounds — deep navy with subtle blue tint
    "--bg-base": "#060b18",
    "--bg-card": "#0c1525",
    "--bg-elevated": "#0a1020",
    "--bg-hover": "#152040",
    "--border": "#1a2744",
    "--border-hover": "#243560",
    // Text
    "--text-primary": "#f0f4ff",
    "--text-secondary": "#c0cce0",
    "--text-muted": "#8899b8",
    "--text-dim": "#5c6e8a",
    "--accent": "#3b82f6",
    // Overlays
    "--overlay": "rgba(4,8,20,.75)",
    "--overlay-heavy": "rgba(4,8,20,.9)",
    "--glass": "rgba(10,16,32,.6)",
    "--shadow": "rgba(0,0,0,.7)",
    // Accent colors — vivid neon on dark
    "--green": "#34d399",
    "--green-bg": "rgba(52,211,153,.12)",
    "--green-border": "rgba(52,211,153,.28)",
    "--yellow": "#facc15",
    "--yellow-bg": "rgba(250,204,21,.10)",
    "--yellow-border": "rgba(250,204,21,.25)",
    "--orange": "#fb923c",
    "--orange-bg": "rgba(251,146,60,.10)",
    "--orange-border": "rgba(251,146,60,.25)",
    "--red": "#fb7185",
    "--red-bg": "rgba(251,113,133,.10)",
    "--red-border": "rgba(251,113,133,.25)",
    "--blue": "#60a5fa",
    "--blue-bg": "rgba(96,165,250,.10)",
    "--blue-border": "rgba(96,165,250,.25)",
    "--purple": "#a78bfa",
    "--purple-bg": "rgba(167,139,250,.10)",
    "--purple-border": "rgba(167,139,250,.25)",
    "--stat-value": "#e8eeff",
  },
  light: {
    // Backgrounds — soft lavender/blue tinted whites
    "--bg-base": "#eef2f9",
    "--bg-card": "#ffffff",
    "--bg-elevated": "#f4f6fb",
    "--bg-hover": "#e2e8f4",
    "--border": "#c8d1e4",
    "--border-hover": "#a8b5d0",
    // Text — strong dark for readability
    "--text-primary": "#111827",
    "--text-secondary": "#1f2937",
    "--text-muted": "#374151",
    "--text-dim": "#4b5563",
    "--accent": "#3b82f6",
    // Overlays
    "--overlay": "rgba(17,24,39,.25)",
    "--overlay-heavy": "rgba(17,24,39,.45)",
    "--glass": "rgba(255,255,255,.8)",
    "--shadow": "rgba(30,50,100,.12)",
    // Accent colors — bold & saturated for light bg
    "--green": "#059669",
    "--green-bg": "rgba(5,150,105,.10)",
    "--green-border": "rgba(5,150,105,.25)",
    "--yellow": "#d97706",
    "--yellow-bg": "rgba(217,119,6,.08)",
    "--yellow-border": "rgba(217,119,6,.22)",
    "--orange": "#ea580c",
    "--orange-bg": "rgba(234,88,12,.08)",
    "--orange-border": "rgba(234,88,12,.22)",
    "--red": "#e11d48",
    "--red-bg": "rgba(225,29,72,.08)",
    "--red-border": "rgba(225,29,72,.22)",
    "--blue": "#2563eb",
    "--blue-bg": "rgba(37,99,235,.08)",
    "--blue-border": "rgba(37,99,235,.22)",
    "--purple": "#7c3aed",
    "--purple-bg": "rgba(124,58,237,.08)",
    "--purple-border": "rgba(124,58,237,.22)",
    "--stat-value": "#111827",
  },
};

function applyTokens(mode: ThemeMode) {
  const root = document.documentElement;
  const map = tokens[mode];
  for (const [key, value] of Object.entries(map)) {
    root.style.setProperty(key, value);
  }
  root.setAttribute("data-theme", mode);
}

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem("traffix-theme");
    return saved === "light" ? "light" : "dark";
  });

  useEffect(() => {
    applyTokens(theme);
    localStorage.setItem("traffix-theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme((p) => (p === "dark" ? "light" : "dark"));

  /** Helper: pick value based on current theme */
  const t = (dark: string, light: string) =>
    theme === "dark" ? dark : light;

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, t }}>
      {children}
    </ThemeContext.Provider>
  );
};
