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

export async function getMyClaims(token) {
  return apiRequest("/api/claims/me", {
    method: "GET",
    token
  });
}

export async function getDemoModeSetting(token) {
  return apiRequest("/api/user/settings/demo-mode", {
    method: "GET",
    token
  });
}

export async function setDemoModeSetting(token, enabled) {
  return apiRequest("/api/user/settings/demo-mode", {
    method: "POST",
    token,
    body: {
      enabled: Boolean(enabled)
    }
  });
}

export async function createDemoClaim(token) {
  return apiRequest("/api/claims/demo", {
    method: "POST",
    token
  });
}

export async function getUserPayoutDetails(token) {
  return apiRequest("/api/user/payout-details", {
    method: "GET",
    token
  });
}

export async function setUserPayoutDetails(token, payload) {
  return apiRequest("/api/user/payout-details", {
    method: "POST",
    token,
    body: {
      account_holder_name: payload.accountHolderName,
      bank_account_number: payload.bankAccountNumber || null,
      ifsc_code: payload.ifscCode || null,
      upi_id: payload.upiId || null
    }
  });
}

export async function createPaymentOrder(token) {
  return apiRequest("/api/payment/create-order", {
    method: "POST",
    token
  });
}

export async function verifyPayment(token, payload) {
  return apiRequest("/api/payment/verify", {
    method: "POST",
    token,
    body: {
      order_id: payload.orderId,
      payment_id: payload.paymentId,
      signature: payload.signature
    }
  });
}
