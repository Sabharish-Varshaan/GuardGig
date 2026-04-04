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
  const minIncome = Number(payload.minIncome);
  const maxIncome = Number(payload.maxIncome);
  const requestBody = {
    full_name: payload.fullName,
    age: Number(payload.age),
    city: payload.city,
    platform: payload.platform,
    vehicle_type: payload.vehicleType,
    work_hours: Number(payload.workHours),
    min_income: minIncome,
    max_income: maxIncome,
    risk_preference: payload.riskPreference
  };

  const response = await apiRequest("/api/onboarding", {
    method: "POST",
    token,
    body: requestBody
  });

  return response;
}

export async function getOnboardingProfile(token) {
  return apiRequest("/api/onboarding/me", {
    method: "GET",
    token
  });
}
