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
  const meanIncome = minIncome > 0 && maxIncome > minIncome ? (minIncome + maxIncome) / 2 : null;
  const incomeVariance =
    meanIncome && meanIncome > 0 ? (maxIncome - minIncome) / meanIncome : 0;

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
      min_income: minIncome,
      max_income: maxIncome,
      mean_income: meanIncome,
      income_variance: incomeVariance,
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
