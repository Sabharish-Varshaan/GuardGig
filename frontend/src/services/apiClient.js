import { API_BASE_URL } from "../config/api";

export async function apiRequest(path, { method = "GET", body, token } = {}) {
  const headers = {
    "Content-Type": "application/json"
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined
    });
  } catch (_error) {
    throw new Error(
      `Network request failed. Ensure backend is running and EXPO_PUBLIC_API_BASE_URL points to a reachable host (current: ${API_BASE_URL}).`
    );
  }

  let payload = null;

  try {
    payload = await response.json();
  } catch (_error) {
    payload = null;
  }

  if (!response.ok) {
    const error = payload?.detail || payload?.message || "Request failed";
    throw new Error(error);
  }

  return payload;
}
