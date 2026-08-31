import { Navigate, Outlet } from "react-router-dom";

import { LoaderCircle } from "lucide-react";

import { useAuth } from "../../context/AuthContext";

function PublicRoute() {
  const { user, isAuthenticated, loading } = useAuth();

  // =====================================================
  // LOADING
  // =====================================================

  if (loading) {
    return (
      <main
        style={{
          display: "grid",
          minHeight: "100vh",
          placeItems: "center",
          background: "#f5f6fb",
          color: "#6d5dfc",
        }}
      >
        <LoaderCircle
          size={34}
          style={{
            animation: "spin 0.8s linear infinite",
          }}
        />
      </main>
    );
  }

  // =====================================================
  // ALREADY AUTHENTICATED
  // =====================================================

  if (isAuthenticated) {
    /*
     * Tavora platform owner
     */
    if (user?.role === "superadmin") {
      return <Navigate to="/owner" replace />;
    }

    /*
     * Restaurant users
     */
    return <Navigate to="/" replace />;
  }

  // =====================================================
  // PUBLIC PAGE
  // =====================================================

  return <Outlet />;
}

export default PublicRoute;
