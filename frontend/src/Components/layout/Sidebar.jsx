import {
  BarChart3,
  ChefHat,
  CreditCard,
  GlassWater,
  LayoutDashboard,
  LogOut,
  Package,
  ReceiptText,
  Settings,
  TableProperties,
} from "lucide-react";

import { useTranslation } from "react-i18next";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

import "./Sidebar.css";

const navigationItems = [
  {
    translationKey: "nav.dashboard",
    path: "/",
    icon: LayoutDashboard,
    roles: ["admin", "cashier", "waiter"],
  },
  {
    translationKey: "nav.tables",
    path: "/tables",
    icon: TableProperties,
    roles: ["admin", "cashier", "waiter"],
  },
  {
    translationKey: "nav.orders",
    path: "/orders",
    icon: ReceiptText,
    roles: ["admin", "cashier", "waiter"],
  },
  {
    translationKey: "nav.kitchen",
    path: "/kitchen",
    icon: ChefHat,
    roles: ["admin", "cashier"],
  },
  {
    translationKey: "nav.bar",
    path: "/bar",
    icon: GlassWater,
    roles: ["admin", "cashier", "waiter"],
  },
  {
    translationKey: "nav.products",
    path: "/products",
    icon: Package,
    roles: ["admin"],
  },
  {
    translationKey: "nav.reports",
    path: "/reports",
    icon: BarChart3,
    roles: ["admin", "cashier"],
  },
  {
    translationKey: "nav.paymentPlan",
    defaultLabel: "Payment Plan",
    path: "/payment-plan",
    icon: CreditCard,
    roles: ["admin"],
  },
  {
    translationKey: "nav.settings",
    path: "/settings",
    icon: Settings,
    roles: ["admin"],
  },
];

function Sidebar() {
  const { t } = useTranslation();

  const navigate = useNavigate();

  const { user, logout } = useAuth();

  const visibleNavigationItems = navigationItems.filter((item) =>
    item.roles.includes(user?.role),
  );

  function handleLogout() {
    const confirmed = window.confirm(t("nav.logoutConfirm"));

    if (!confirmed) {
      return;
    }

    logout();

    navigate("/login", {
      replace: true,
    });
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-logo">T</div>

        <div className="sidebar-brand-content">
          <strong>Tavora POS</strong>
          <span>{t("nav.managementSystem")}</span>
        </div>
      </div>

      <nav className="sidebar-navigation">
        {visibleNavigationItems.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                isActive
                  ? "sidebar-navigation-link sidebar-navigation-link-active"
                  : "sidebar-navigation-link"
              }
            >
              <Icon size={19} />

              <span>
                {t(item.translationKey, {
                  defaultValue: item.defaultLabel,
                })}
              </span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-user-avatar">
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>

          <div className="sidebar-user-info">
            <strong>{user?.name || "Tavora User"}</strong>
            <span>{user?.role || "user"}</span>
          </div>
        </div>

        <button
          type="button"
          className="sidebar-logout-button"
          onClick={handleLogout}
        >
          <LogOut size={18} />
          <span>{t("nav.logout")}</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
