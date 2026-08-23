import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  clearAuthentication,
  getCurrentUser,
  getStoredToken,
  getStoredUser,
  saveAuthentication,
} from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [loading, setLoading] = useState(true);

  async function validateAuthentication() {
    const token = getStoredToken();

    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const currentUser = await getCurrentUser();

      localStorage.setItem("tavora_user", JSON.stringify(currentUser));

      setUser(currentUser);
    } catch (error) {
      console.error("Authentication validation failed:", error);

      clearAuthentication();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    validateAuthentication();
  }, []);

  function login(authenticationData) {
    saveAuthentication(authenticationData);
    setUser(authenticationData.user);
  }

  function logout() {
    clearAuthentication();
    setUser(null);
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      refreshUser: validateAuthentication,
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}
