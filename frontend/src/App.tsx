import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Navbar } from "./components/layout/Navbar";
import { Dashboard } from "./pages/Dashboard";
import { Settings } from "./pages/Settings";
import { LiveMap } from "./pages/Livemap";
import { LoginPage } from "./pages/Login";
import { ThemeProvider } from "./lib/ThemeContext";
import { AuthProvider, useAuth } from "./lib/AuthContext";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 3000 } },
});

function AppShell() {
  const { isAuthenticated } = useAuth();
  const [page, setPage] = useState("dashboard");

  if (!isAuthenticated) return <LoginPage />;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        background: "var(--bg-base)",
        transition: "background .3s ease",
      }}
    >
      <Navbar page={page} onNavigate={setPage} />
      <main style={{ flex: 1, overflow: "auto" }}>
        {page === "dashboard" && <Dashboard />}
        {page === "map" && <LiveMap />}
        {page === "settings" && <Settings />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <AppShell />
        </QueryClientProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
