import { apiRequest } from "./apiClient";

export async function createPolicy(token) {
  return apiRequest("/api/policy/create", {
    method: "POST",
    token
  });
}

export async function getMyPolicy(token) {
  return apiRequest("/api/policy/me", {
    method: "GET",
    token
  });
}

export async function checkTrigger({ lat, lon }) {
  return apiRequest("/api/trigger/check", {
    method: "POST",
    body: {
      lat,
      lon
    }
  });
}

export async function createClaim(token, payload) {
  return apiRequest("/api/claim/create", {
    method: "POST",
    token,
    body: {
      lat: payload.lat,
      lon: payload.lon,
      activity_status: payload.activityStatus
    }
  });
}

export async function getMyClaims(token) {
  return apiRequest("/api/claims/me", {
    method: "GET",
    token
  });
}
