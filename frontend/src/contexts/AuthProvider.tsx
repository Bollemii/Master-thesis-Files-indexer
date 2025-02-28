import { useState } from "react";
import { AuthContext } from "./AuthContext";
import { AUTH_TOKEN_KEY } from "../constants/Auth";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem(AUTH_TOKEN_KEY)
  );

  const login = (token: string) => {
    setToken(token);
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  };

  const logout = () => {
    setToken(null);
    localStorage.removeItem(AUTH_TOKEN_KEY);
  };

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
