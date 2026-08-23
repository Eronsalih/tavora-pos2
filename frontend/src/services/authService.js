import api from "./api";

export async function loginUser(credentials) {
  const response = await api.post("/api/auth/login", credentials);

  return response.data;
}
export async function loginWithPin(pin) {
  const response = await api.post("/api/auth/pin-login", {
    pin,
  });

  return response.data;
}
export async function getCurrentUser() {
  const response = await api.get("/api/auth/me");

  return response.data;
}

export function getStoredUser() {
  const storedUser = localStorage.getItem("tavora_user");

  if (!storedUser) {
    return null;
  }

  try {
    return JSON.parse(storedUser);
  } catch {
    localStorage.removeItem("tavora_user");

    return null;
  }
}

export function getStoredToken() {
  return localStorage.getItem("tavora_access_token");
}

export function saveAuthentication(data) {
  localStorage.setItem("tavora_access_token", data.access_token);
  localStorage.setItem("tavora_user", JSON.stringify(data.user));
}

export function clearAuthentication() {
  localStorage.removeItem("tavora_access_token");
  localStorage.removeItem("tavora_user");
}
