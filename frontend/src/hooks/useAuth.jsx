import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./../api/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;

    if (!getToken()) {
      setLoading(false);
      return undefined;
    }

    api
      .me()
      .then((record) => {
        if (alive) setUser(record);
      })
      .catch(() => setToken(null))
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const result = await api.login({ email, password });
    setToken(result.access_token);
    setUser(await api.me());
  }, []);

  const register = useCallback(async (data) => {
    const result = await api.register(data);
    setToken(result.access_token);
    setUser(await api.me());
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}