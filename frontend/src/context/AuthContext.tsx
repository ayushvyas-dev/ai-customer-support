"use client";

import * as React from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, getToken, removeToken } from "@/lib/api";

interface AuthContextType {
  user: string | null;
  loading: boolean;
  login: (username: string, pass: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = React.createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const router = useRouter();
  const pathname = usePathname();

  React.useEffect(() => {
    async function checkAuth() {
      const token = getToken();
      if (!token) {
        setUser(null);
        setLoading(false);
        if (pathname !== "/login") {
          router.replace("/login");
        }
        return;
      }

      try {
        const res = await api.me();
        setUser(res.username);
        if (pathname === "/login") {
          router.replace("/events");
        }
      } catch {
        removeToken();
        setUser(null);
        if (pathname !== "/login") {
          router.replace("/login");
        }
      } finally {
        setLoading(false);
      }
    }

    checkAuth();
  }, [pathname, router]);

  const login = async (username: string, pass: string) => {
    const res = await api.login(username, pass);
    setUser(res.username);
    router.replace("/events");
  };

  const logout = () => {
    removeToken();
    setUser(null);
    router.replace("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return React.useContext(AuthContext);
}

