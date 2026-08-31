import api from "./api";

const TOKEN_STORAGE_KEY = "tavora_access_token";
const USER_STORAGE_KEY = "tavora_user";
const BUSINESS_STORAGE_KEY = "tavora_business_id";

// =========================================================
// EMAIL / PASSWORD LOGIN
// =========================================================

export async function loginUser(credentials) {
  const response = await api.post("/api/auth/login", credentials);

  return response.data;
}

// =========================================================
// PIN LOGIN
// =========================================================

export async function loginWithPin(pin) {
  const businessId = getStoredBusinessId();

  if (!businessId) {
    const error = new Error("This device is not linked to a Tavora business.");

    error.code = "BUSINESS_NOT_CONFIGURED";

    throw error;
  }

  const response = await api.post("/api/auth/pin-login", {
    business_id: businessId,
    pin,
  });

  return response.data;
}

// =========================================================
// CURRENT USER
// =========================================================

export async function getCurrentUser() {
  const response = await api.get("/api/auth/me");

  return response.data;
}

// =========================================================
// SUBSCRIPTION
// =========================================================

export async function getSubscription() {
  const response = await api.get("/api/auth/subscription");

  return response.data;
}

// =========================================================
// STORED USER
// =========================================================

export function getStoredUser() {
  const storedUser = localStorage.getItem(USER_STORAGE_KEY);

  if (!storedUser) {
    return null;
  }

  try {
    return JSON.parse(storedUser);
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY);

    return null;
  }
}

// =========================================================
// STORED TOKEN
// =========================================================

export function getStoredToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

// =========================================================
// STORED BUSINESS
// =========================================================

export function getStoredBusinessId() {
  const businessId = localStorage.getItem(BUSINESS_STORAGE_KEY);

  if (!businessId) {
    return null;
  }

  return businessId;
}

// =========================================================
// SAVE BUSINESS FOR THIS DEVICE
// =========================================================

export function saveBusinessId(businessId) {
  if (!businessId) {
    return;
  }

  localStorage.setItem(BUSINESS_STORAGE_KEY, businessId);
}

// =========================================================
// SAVE AUTHENTICATION
// =========================================================

export function saveAuthentication(data) {
  localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);

  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(data.user));

  /*
   * A normal restaurant user contains business_id.
   *
   * We keep this business ID on the device even after
   * logout so employees can later log in only with PIN.
   *
   * Superadmin has no business_id and therefore does not
   * change the restaurant assigned to this device.
   */
  if (data.user?.business_id && data.user?.role !== "superadmin") {
    saveBusinessId(data.user.business_id);
  }
}

// =========================================================
// CLEAR AUTHENTICATION
// =========================================================

export function clearAuthentication() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);

  localStorage.removeItem(USER_STORAGE_KEY);

  /*
   * IMPORTANT:
   *
   * Do NOT remove tavora_business_id here.
   *
   * Logout removes the current session only.
   * The Tavora installation/browser remains linked
   * to the restaurant so employees can use PIN login.
   */
}

// =========================================================
// REMOVE DEVICE BUSINESS
// =========================================================

export function clearStoredBusinessId() {
  localStorage.removeItem(BUSINESS_STORAGE_KEY);
}

// =========================================================
// SIGNUP
// =========================================================

export async function signupUser(data) {
  const response = await api.post("/api/auth/signup", data);

  return response.data;
}
