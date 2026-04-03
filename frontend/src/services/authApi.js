import { apiRequest } from "./apiClient";

export async function registerUser({ fullName, phone, password }) {
  return apiRequest("/api/auth/register", {
    method: "POST",
    body: {
      full_name: fullName,
      phone,
      password
    }
  });
}

export async function loginUser({ phone, password }) {
  return apiRequest("/api/auth/login", {
    method: "POST",
    body: {
      phone,
      password
    }
  });
}

export async function submitOnboardingProfile(payload, token) {
  return apiRequest("/api/onboarding", {
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
      risk_preference: payload.riskPreference
    }
  });
}

export async function getOnboardingProfile(token) {
  return apiRequest("/api/onboarding/me", {
    method: "GET",
    token
  });
}
