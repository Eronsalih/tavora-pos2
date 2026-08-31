import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import ProtectedRoute from "../Components/auth/ProtectedRoute";
import PublicRoute from "../Components/auth/PublicRoute";
import RoleRoute from "../Components/auth/RoleRoute";
import SubscriptionRoute from "../Components/auth/SubscriptionRoute";

import MainLayout from "../layouts/MainLayout";
import OwnerLayout from "../layouts/OwnerLayout";

import Dashboard from "../Pages/Dashboard/Dashboard";
import Kitchen from "../Pages/Kitchen/Kitchen";
import Login from "../Pages/Login/Login";
import Register from "../Pages/Register/Register";
import PaymentPlan from "../Pages/PaymentPlan/PaymentPlan";
import Orders from "../Pages/Orders/Orders";
import Products from "../Pages/Products/Products";
import Reports from "../Pages/Reports/Reports";
import Settings from "../Pages/Settings/Settings";
import Tables from "../Pages/Tables/Tables";
import Bar from "../Pages/Bar/Bar";

import OwnerDashboard from "../Pages/Owner/Dashboard/OwnerDashboard";
import OwnerBusinesses from "../Pages/Owner/Businesses/OwnerBusinesses";
import OwnerBusinessDetails from "../Pages/Owner/Businesses/OwnerBusinessDetails";
import OwnerSubscriptions from "../Pages/Owner/Subscriptions/OwnerSubscriptions";
import OwnerPayments from "../Pages/Owner/Payments/OwnerPayments";

const TENANT_ROLES = ["admin", "cashier", "waiter"];

// =========================================================
// ROOT REDIRECT
// =========================================================

function RootRedirect() {
  const { user } = useAuth();

  if (user?.role === "superadmin") {
    return <Navigate to="/owner" replace />;
  }

  return <Navigate to="/dashboard" replace />;
}

// =========================================================
// TENANT ROUTE
// =========================================================

function TenantRoute() {
  const { user } = useAuth();

  if (user?.role === "superadmin") {
    return <Navigate to="/owner" replace />;
  }

  if (!TENANT_ROLES.includes(user?.role)) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

// =========================================================
// OWNER ROUTE
// =========================================================

function OwnerRoute() {
  const { user } = useAuth();

  if (user?.role !== "superadmin") {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

// =========================================================
// APP ROUTES
// =========================================================

function AppRoutes() {
  return (
    <Routes>
      {/* ================================================= */}
      {/* PUBLIC */}
      {/* ================================================= */}

      <Route element={<PublicRoute />}>
        <Route path="/login" element={<Login />} />

        <Route path="/register" element={<Register />} />
      </Route>

      {/* ================================================= */}
      {/* AUTHENTICATED */}
      {/* ================================================= */}

      <Route element={<ProtectedRoute />}>
        {/* ROOT */}

        <Route path="/" element={<RootRedirect />} />

        {/* ============================================= */}
        {/* OWNER SYSTEM */}
        {/* ============================================= */}

        <Route element={<OwnerRoute />}>
          <Route path="/owner" element={<OwnerLayout />}>
            <Route index element={<OwnerDashboard />} />

            <Route path="businesses" element={<OwnerBusinesses />} />

            <Route
              path="businesses/:businessId"
              element={<OwnerBusinessDetails />}
            />

            <Route path="subscriptions" element={<OwnerSubscriptions />} />

            <Route path="payments" element={<OwnerPayments />} />
          </Route>
        </Route>

        {/* ============================================= */}
        {/* TENANT SYSTEM */}
        {/* ============================================= */}

        <Route element={<TenantRoute />}>
          {/* PAYMENT PLAN */}

          <Route element={<RoleRoute allowedRoles={["admin"]} />}>
            <Route path="/payment-plan" element={<PaymentPlan />} />
          </Route>

          {/* =========================================== */}
          {/* ACTIVE SUBSCRIPTION */}
          {/* =========================================== */}

          <Route element={<SubscriptionRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />

              <Route path="/tables" element={<Tables />} />

              <Route path="/orders" element={<Orders />} />

              <Route path="/bar" element={<Bar />} />

              {/* ===================================== */}
              {/* ADMIN + CASHIER */}
              {/* ===================================== */}

              <Route
                element={<RoleRoute allowedRoles={["admin", "cashier"]} />}
              >
                <Route path="/kitchen" element={<Kitchen />} />

                <Route path="/reports" element={<Reports />} />
              </Route>

              {/* ===================================== */}
              {/* ADMIN ONLY */}
              {/* ===================================== */}

              <Route element={<RoleRoute allowedRoles={["admin"]} />}>
                <Route path="/products" element={<Products />} />

                <Route path="/settings" element={<Settings />} />
              </Route>
            </Route>
          </Route>
        </Route>
      </Route>

      {/* ================================================= */}
      {/* FALLBACK */}
      {/* ================================================= */}

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default AppRoutes;
