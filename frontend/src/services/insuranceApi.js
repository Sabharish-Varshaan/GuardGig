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
