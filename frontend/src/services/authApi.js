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

  console.log("[Onboarding] Request payload", requestBody);

  const response = await apiRequest("/api/onboarding", {
    method: "POST",
    token,
    body: requestBody
  });

  console.log("[Onboarding] Response profile fields", {
    mean_income: response?.profile?.mean_income,
    income_variance: response?.profile?.income_variance
  });

  return response;
}

export async function getOnboardingProfile(token) {
  return apiRequest("/api/onboarding/me", {
    method: "GET",
    token
  });
}
