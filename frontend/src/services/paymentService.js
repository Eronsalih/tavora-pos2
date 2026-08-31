import api from "./api";

export async function createSubscriptionPayment({
  plan = "pro_monthly",
  currency = "EUR",
} = {}) {
  const response = await api.post("/api/payments/create", {
    plan,
    currency,
  });

  return response.data;
}

export async function simulatePaymentSuccess(paymentId) {
  const response = await api.post(
    `/api/payments/${paymentId}/simulate-success`,
  );

  return response.data;
}
