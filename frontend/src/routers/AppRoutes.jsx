import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "../Components/auth/ProtectedRoute";
import PublicRoute from "../Components/auth/PublicRoute";
import RoleRoute from "../Components/auth/RoleRoute";

import MainLayout from "../layouts/MainLayout";

import Dashboard from "../Pages/Dashboard/Dashboard";
import Kitchen from "../Pages/Kitchen/Kitchen";
import Login from "../Pages/Login/Login";
import Orders from "../Pages/Orders/Orders";
import Products from "../Pages/Products/Products";
import Reports from "../Pages/Reports/Reports";
import Settings from "../Pages/Settings/Settings";
import Tables from "../Pages/Tables/Tables";
import Bar from "../Pages/Bar/Bar";

function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<Login />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route index element={<Dashboard />} />

          <Route path="/tables" element={<Tables />} />

          <Route path="/orders" element={<Orders />} />
          <Route path="/bar" element={<Bar />} />
          <Route element={<RoleRoute allowedRoles={["admin", "cashier"]} />}>
            <Route path="/kitchen" element={<Kitchen />} />
            <Route path="/reports" element={<Reports />} />
          </Route>

          <Route element={<RoleRoute allowedRoles={["admin"]} />}>
            <Route path="/products" element={<Products />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default AppRoutes;
