import { API_BASE_URL } from "../config/api";

async function request(path, { method = "GET", body, token } = {}) {
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
  } catch (_) {
    throw new Error(
      `Network request failed. Ensure backend is running and EXPO_PUBLIC_API_BASE_URL points to a reachable host (current: ${API_BASE_URL}).`
    );
  }

  let payload = null;

  try {
    payload = await response.json();
  } catch (_) {
    payload = null;
  }

  if (!response.ok) {
    const error = payload?.detail || payload?.message || "Request failed";
    throw new Error(error);
  }

  return payload;
}

export async function registerUser({ fullName, phone, password }) {
  return request("/api/auth/register", {
    method: "POST",
    body: {
      full_name: fullName,
      phone,
      password
    }
  });
}

export async function loginUser({ phone, password }) {
  return request("/api/auth/login", {
    method: "POST",
    body: {
      phone,
      password
    }
  });
}

export async function submitOnboardingProfile(payload, token) {
  return request("/api/onboarding", {
    method: "POST",
    token,
    body: {
      full_name: payload.fullName,
      age: Number(payload.age),
      city: payload.city,
      platform: payload.platform,
      vehicle_type: payload.vehicleType,
      work_hours: Number(payload.workHours),
      daily_income: Number(payload.dailyIncome),
      weekly_income: Number(payload.weeklyIncome),
      risk_preference: payload.riskPreference
    }
  });
}

export async function getOnboardingProfile(token) {
  return request("/api/onboarding/me", {
    method: "GET",
    token
  });
}
