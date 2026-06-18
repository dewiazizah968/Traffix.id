import { createContext, useContext, useState, type ReactNode } from "react";

export interface User {
  username: string;
  role: string;
  avatar: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => string | null;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  login: () => "Not implemented",
  logout: () => {},
  isAuthenticated: false,
});

export const useAuth = () => useContext(AuthContext);

/* ── Dummy credentials ── */
const DUMMY_USERS: Record<
  string,
  { password: string; role: string; name: string }
> = {
  admin: { password: "admin123", role: "Administrator", name: "Admin Traffix" },
};

const STORAGE_KEY = "traffix-auth";

function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(loadUser);

  const login = (username: string, password: string): string | null => {
    const entry = DUMMY_USERS[username.toLowerCase()];
    if (!entry) return "Username tidak ditemukan";
    if (entry.password !== password) return "Password salah";

    const u: User = {
      username: username.toLowerCase(),
      role: entry.role,
      avatar: entry.name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .toUpperCase()
        .slice(0, 2),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(u));
    setUser(u);
    return null; // no error
  };

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, login, logout, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
};
