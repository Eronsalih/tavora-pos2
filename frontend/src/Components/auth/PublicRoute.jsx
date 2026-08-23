import { Navigate, Outlet } from "react-router-dom";
import { LoaderCircle } from "lucide-react";

import { useAuth } from "../../context/AuthContext";

function PublicRoute() {
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
        <LoaderCircle
          size={34}
          style={{
            animation: "spin 0.8s linear infinite",
          }}
        />
      </main>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

export default PublicRoute;
