import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  clearAuthentication,
  getCurrentUser,
  getStoredToken,
  getStoredUser,
  getSubscription,
  saveAuthentication,
} from "../services/authService";

const AuthContext = createContext(null);

function isPlatformSuperadmin(user) {
  return user?.role === "superadmin";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());

  const [loading, setLoading] = useState(true);

  const [subscription, setSubscription] = useState(null);

  const [subscriptionLoading, setSubscriptionLoading] = useState(true);

  const [subscriptionError, setSubscriptionError] = useState("");

  // =====================================================
  // REFRESH SUBSCRIPTION
  // =====================================================

  const refreshSubscription = useCallback(async (userOverride = null) => {
    const token = getStoredToken();

    const currentUser = userOverride || getStoredUser();

    if (!token) {
      setSubscription(null);
      setSubscriptionError("");
      setSubscriptionLoading(false);

      return null;
    }

    /*
     * Superadmin is the Tavora platform owner.
     * It is not attached to a restaurant/business
     * and therefore has no tenant subscription.
     */
    if (isPlatformSuperadmin(currentUser)) {
      setSubscription(null);
      setSubscriptionError("");
      setSubscriptionLoading(false);

      return null;
    }

    setSubscriptionLoading(true);
    setSubscriptionError("");

    try {
      const currentSubscription = await getSubscription();

      setSubscription(currentSubscription);

      return currentSubscription;
    } catch (error) {
      console.error("Subscription validation failed:", error);

      if (error.response?.status === 401) {
        clearAuthentication();

        setUser(null);
        setSubscription(null);

        return null;
      }

      setSubscription(null);

      const detail = error.response?.data?.detail;

      setSubscriptionError(
        typeof detail === "string"
          ? detail
          : "Subscription could not be verified.",
      );

      return null;
    } finally {
      setSubscriptionLoading(false);
    }
  }, []);

  // =====================================================
  // VALIDATE AUTHENTICATION
  // =====================================================

  const validateAuthentication = useCallback(async () => {
    const token = getStoredToken();

    if (!token) {
      setUser(null);
      setSubscription(null);

      setLoading(false);
      setSubscriptionLoading(false);

      return;
    }

    setLoading(true);

    try {
      const currentUser = await getCurrentUser();

      localStorage.setItem("tavora_user", JSON.stringify(currentUser));

      setUser(currentUser);

      await refreshSubscription(currentUser);
    } catch (error) {
      console.error("Authentication validation failed:", error);

      clearAuthentication();

      setUser(null);
      setSubscription(null);

      setSubscriptionError("");
      setSubscriptionLoading(false);
    } finally {
      setLoading(false);
    }
  }, [refreshSubscription]);

  useEffect(() => {
    validateAuthentication();
  }, [validateAuthentication]);

  // =====================================================
  // LOGIN
  // =====================================================

  const login = useCallback(
    async (authenticationData) => {
      saveAuthentication(authenticationData);

      const authenticatedUser = authenticationData.user;

      setUser(authenticatedUser);

      setSubscription(null);
      setSubscriptionError("");

      /*
       * Tavora owner does not have a restaurant
       * subscription.
       */
      if (isPlatformSuperadmin(authenticatedUser)) {
        setSubscriptionLoading(false);

        return null;
      }

      setSubscriptionLoading(true);

      return refreshSubscription(authenticatedUser);
    },
    [refreshSubscription],
  );

  // =====================================================
  // LOGOUT
  // =====================================================

  const logout = useCallback(() => {
    clearAuthentication();

    setUser(null);
    setSubscription(null);

    setSubscriptionError("");
    setSubscriptionLoading(false);
  }, []);

  // =====================================================
  // SUBSCRIPTION STATUS
  // =====================================================

  const isSubscriptionActive = useMemo(() => {
    /*
     * Superadmin is not a tenant.
     * Subscription rules belong only
     * to restaurant/business accounts.
     */
    if (isPlatformSuperadmin(user)) {
      return true;
    }

    if (subscription?.status !== "active") {
      return false;
    }

    if (!subscription.expires_at) {
      return true;
    }

    const expirationTime = new Date(subscription.expires_at).getTime();

    if (Number.isNaN(expirationTime)) {
      return false;
    }

    return expirationTime > Date.now();
  }, [user, subscription]);

  // =====================================================
  // CONTEXT VALUE
  // =====================================================

  const value = useMemo(
    () => ({
      user,
      loading,

      subscription,
      subscriptionLoading,
      subscriptionError,

      isAuthenticated: Boolean(user),

      isSubscriptionActive,

      isSuperadmin: isPlatformSuperadmin(user),

      login,
      logout,

      refreshUser: validateAuthentication,

      refreshSubscription,
    }),
    [
      user,
      loading,

      subscription,
      subscriptionLoading,
      subscriptionError,

      isSubscriptionActive,

      login,
      logout,

      validateAuthentication,
      refreshSubscription,
    ],
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
