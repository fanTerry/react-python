import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import * as authApi from "../api/auth";
import { clearToken, getToken, isApiError, setToken } from "../api/client";
import type { User } from "../types/auth";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<string | null>;
  register: (
    username: string,
    password: string,
    email?: string,
  ) => Promise<string | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    const result = await authApi.fetchMe();
    if (isApiError(result)) {
      clearToken();
      setUser(null);
    } else {
      setUser(result);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (username: string, password: string) => {
    const result = await authApi.login(username, password);
    if (isApiError(result)) return result.message;
    setToken(result.access_token);
    setUser(result.user);
    return null;
  };

  const register = async (
    username: string,
    password: string,
    email?: string,
  ) => {
    const result = await authApi.register(username, password, email);
    if (isApiError(result)) return result.message;
    setToken(result.access_token);
    setUser(result.user);
    return null;
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
