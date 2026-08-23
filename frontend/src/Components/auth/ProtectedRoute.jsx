import { Navigate, Outlet, useLocation } from "react-router-dom";
import { LoaderCircle } from "lucide-react";

import { useAuth } from "../../context/AuthContext";

function ProtectedRoute() {
  const location = useLocation();

  const { isAuthenticated, loading } = useAuth();

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
        <div
          style={{
            display: "grid",
            justifyItems: "center",
            gap: "12px",
          }}
        >
          <LoaderCircle
            size={34}
            style={{
              animation: "spin 0.8s linear infinite",
            }}
          />

          <span>Duke verifikuar sesionin...</span>
        </div>
      </main>
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  return <Outlet />;
}

export default ProtectedRoute;
