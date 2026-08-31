import api from "./api";

const PLATFORM_ADMIN_BASE_URL = "/api/platform-admin";

// =========================================================
// DASHBOARD
// =========================================================

export async function getPlatformDashboard() {
  const response = await api.get(`${PLATFORM_ADMIN_BASE_URL}/dashboard`);

  return response.data;
}

// =========================================================
// BUSINESSES
// =========================================================

export async function getPlatformBusinesses(params = {}) {
  const response = await api.get(`${PLATFORM_ADMIN_BASE_URL}/businesses`, {
    params,
  });

  return response.data;
}

export async function getPlatformBusinessById(businessId) {
  if (!businessId) {
    throw new Error("Business ID is required.");
  }

  const response = await api.get(
    `${PLATFORM_ADMIN_BASE_URL}/businesses/${businessId}`,
  );

  return response.data;
}

// =========================================================
// SUBSCRIPTIONS
// =========================================================

export async function getPlatformSubscriptions(params = {}) {
  const response = await api.get(`${PLATFORM_ADMIN_BASE_URL}/subscriptions`, {
    params,
  });

  return response.data;
}

// =========================================================
// PAYMENTS
// =========================================================

export async function getPlatformPayments(params = {}) {
  const response = await api.get(`${PLATFORM_ADMIN_BASE_URL}/payments`, {
    params,
  });

  return response.data;
}
