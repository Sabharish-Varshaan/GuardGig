import { apiRequest } from "./apiClient";
import { API_BASE_URL } from "../config/api";

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
  const body = {
    lat: payload.lat,
    lon: payload.lon
  };

  if (payload.activityStatus) {
    body.activity_status = payload.activityStatus;
  }

  return apiRequest("/api/claim/create", {
    method: "POST",
    token,
    body
  });
}

export async function getMyClaims(token) {
  return apiRequest("/api/claims/me", {
    method: "GET",
    token
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
      payment_id: payload.paymentId
    }
  });
}

export function buildHostedPaymentUrl({ orderId, amount, currency, keyId }) {
  const params = new URLSearchParams({
    order_id: orderId || "",
    amount: String(amount || 0),
    currency: currency || "INR",
    key_id: keyId || ""
  });

  return `${API_BASE_URL}/payment-pages/payment.html?${params.toString()}`;
}
