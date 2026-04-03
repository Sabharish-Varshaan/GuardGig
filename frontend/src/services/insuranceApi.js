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

export async function checkTrigger(location) {
  return apiRequest("/api/trigger/check", {
    method: "POST",
    body: {
      location
    }
  });
}

export async function createClaim(token, payload) {
  return apiRequest("/api/claim/create", {
    method: "POST",
    token,
    body: {
      location: payload.location,
      activity_status: payload.activityStatus || "active",
      location_valid: payload.locationValid !== false
    }
  });
}

export async function getMyClaims(token) {
  return apiRequest("/api/claims/me", {
    method: "GET",
    token
  });
}
