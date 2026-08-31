import { useState } from "react";

import {
  Building2,
  Check,
  CreditCard,
  Crown,
  LoaderCircle,
  ShieldCheck,
  Store,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import {
  createSubscriptionPayment,
  simulatePaymentSuccess,
} from "../../services/paymentService";

import { useAuth } from "../../context/AuthContext";

import "./PaymentPlan.css";

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    description:
      "Për kafiteri dhe lokale të vogla që duan një POS modern dhe të thjeshtë.",
    icon: Store,

    monthly: {
      key: "starter_monthly",
      price: 24.9,
    },

    yearly: {
      key: "starter_yearly",
      price: 249,
    },

    features: [
      "Menaxhimi i tavolinave",
      "Porositë dhe pagesat",
      "Menaxhimi i produkteve",
      "Cash & Card",
      "Admin dhe Waiter",
      "Raporte bazike",
      "Desktop App me Electron",
    ],
  },

  {
    id: "pro",
    name: "Pro",
    description:
      "Paketa kryesore për restorante, lounge dhe kafiteri që duan menaxhim të plotë.",
    icon: Crown,
    popular: true,

    monthly: {
      key: "pro_monthly",
      price: 39.9,
    },

    yearly: {
      key: "pro_yearly",
      price: 399,
    },

    features: [
      "Gjithçka nga Starter",
      "Kitchen Management",
      "Bar Management",
      "Reports të avancuara",
      "Admin, Cashier dhe Waiter",
      "PIN login për punonjësit",
      "3 gjuhë: AL / EN / DE",
      "Cloud access",
      "Desktop App me Electron",
    ],
  },

  {
    id: "business",
    name: "Business",
    description:
      "Për lokale më të mëdha dhe biznese që duan më shumë kontroll, support prioritar dhe mundësi për zgjerim.",
    icon: Building2,

    monthly: {
      key: "business_monthly",
      price: 59.9,
    },

    yearly: {
      key: "business_yearly",
      price: 599,
    },

    features: [
      "Gjithçka nga Pro",
      "Priority Support",
      "Priority Onboarding & Setup",
      "Setup për më shumë pajisje / terminale",
      "Owner controls të avancuara",
      "Raporte dhe analiza të zgjeruara",
      "Multi-location Dashboard — Coming soon",
      "Priority feature requests",
    ],
  },
];

function getPlanTier(planKey) {
  const normalizedPlan = String(planKey || "").toLowerCase();

  if (normalizedPlan.startsWith("starter")) {
    return "starter";
  }

  if (normalizedPlan.startsWith("business")) {
    return "business";
  }

  if (normalizedPlan.startsWith("pro")) {
    return "pro";
  }

  return null;
}

function getBillingPeriod(planKey) {
  const normalizedPlan = String(planKey || "").toLowerCase();

  if (normalizedPlan.endsWith("_yearly")) {
    return "yearly";
  }

  return "monthly";
}

function formatPrice(value) {
  const price = Number(value);

  if (Number.isInteger(price)) {
    return `€${price}`;
  }

  return `€${price.toFixed(2)}`;
}

function formatExpiration(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("sq-AL", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(date);
}

function PaymentPlan() {
  const navigate = useNavigate();

  const { subscription, isSubscriptionActive, refreshSubscription } = useAuth();

  const [billingPeriod, setBillingPeriod] = useState("monthly");

  const [loadingPlanKey, setLoadingPlanKey] = useState(null);

  const [createdPayment, setCreatedPayment] = useState(null);

  const [createdPlanKey, setCreatedPlanKey] = useState(null);

  const [message, setMessage] = useState("");

  const [error, setError] = useState("");

  const isDevelopment = import.meta.env.DEV;

  const currentTier = getPlanTier(subscription?.plan);

  const currentBillingPeriod = getBillingPeriod(subscription?.plan);

  function resetMessages() {
    setMessage("");
    setError("");
  }

  async function handleChoosePlan(plan) {
    const selectedOption = plan[billingPeriod];

    if (!selectedOption) {
      return;
    }

    resetMessages();

    setLoadingPlanKey(selectedOption.key);

    setCreatedPayment(null);
    setCreatedPlanKey(null);

    try {
      const payment = await createSubscriptionPayment({
        plan: selectedOption.key,
        currency: "EUR",
      });

      setCreatedPayment(payment);

      setCreatedPlanKey(selectedOption.key);

      setMessage(
        `Pagesa për Tavora ${plan.name} u krijua me sukses. Status: ${payment.status}.`,
      );

      console.log("Tavora payment:", payment);
    } catch (err) {
      console.error("Payment creation failed:", err);

      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string" ? detail : "Pagesa nuk mund të krijohet.",
      );
    } finally {
      setLoadingPlanKey(null);
    }
  }

  async function handleSimulateSuccess() {
    if (!createdPayment?.id) {
      return;
    }

    resetMessages();

    setLoadingPlanKey(createdPlanKey);

    try {
      const payment = await simulatePaymentSuccess(createdPayment.id);

      setCreatedPayment(payment);

      const currentSubscription = await refreshSubscription();

      const activatedTier = getPlanTier(currentSubscription?.plan);

      setMessage(
        `Pagesa u kompletua me sukses. Tavora ${
          activatedTier
            ? activatedTier.charAt(0).toUpperCase() + activatedTier.slice(1)
            : ""
        } është aktive.`,
      );
    } catch (err) {
      console.error("Payment simulation failed:", err);

      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string" ? detail : "Simulimi i pagesës dështoi.",
      );
    } finally {
      setLoadingPlanKey(null);
    }
  }

  return (
    <main className="payment-plan-page">
      <section className="payment-plan-container">
        <header className="payment-plan-header">
          <div>
            <p className="payment-plan-eyebrow">Tavora Subscription</p>

            <h1>Plans</h1>

            <p className="payment-plan-header-description">
              Zgjidh planin që i përshtatet biznesit tënd. Mund të paguash çdo
              muaj ose të kursesh me pagesën vjetore.
            </p>
          </div>

          {isSubscriptionActive && (
            <button
              type="button"
              className="payment-plan-dashboard-button"
              onClick={() => navigate("/")}
            >
              Kthehu në Dashboard
            </button>
          )}
        </header>

        {isSubscriptionActive && (
          <section className="payment-plan-current">
            <div className="payment-plan-current-icon">
              <ShieldCheck size={22} />
            </div>

            <div className="payment-plan-current-info">
              <span>Your Plan</span>

              <strong>
                Tavora{" "}
                {currentTier
                  ? currentTier.charAt(0).toUpperCase() + currentTier.slice(1)
                  : subscription?.plan}
              </strong>

              <small>
                {currentBillingPeriod === "yearly" ? "Vjetor" : "Mujor"}
                {" • "}
                Aktiv deri më {formatExpiration(subscription?.expires_at)}
              </small>
            </div>

            <div className="payment-plan-active-badge">Active</div>
          </section>
        )}

        <div className="payment-plan-billing-wrapper">
          <div className="payment-plan-billing-toggle">
            <button
              type="button"
              className={
                billingPeriod === "monthly"
                  ? "payment-plan-billing-button payment-plan-billing-button-active"
                  : "payment-plan-billing-button"
              }
              onClick={() => setBillingPeriod("monthly")}
            >
              Monthly
            </button>

            <button
              type="button"
              className={
                billingPeriod === "yearly"
                  ? "payment-plan-billing-button payment-plan-billing-button-active"
                  : "payment-plan-billing-button"
              }
              onClick={() => setBillingPeriod("yearly")}
            >
              Yearly
              <span>Save ~17%</span>
            </button>
          </div>
        </div>

        {message && (
          <div className="payment-plan-message payment-plan-message-success">
            <ShieldCheck size={19} />

            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="payment-plan-message payment-plan-message-error">
            <span>{error}</span>
          </div>
        )}

        <div className="payment-plan-grid">
          {PLANS.map((plan) => {
            const PlanIcon = plan.icon;

            const selectedOption = plan[billingPeriod];

            const isCurrentPlan =
              isSubscriptionActive &&
              currentTier === plan.id &&
              currentBillingPeriod === billingPeriod;

            const isLoading = loadingPlanKey === selectedOption.key;

            const hasPendingPayment =
              createdPayment?.status === "pending" &&
              createdPlanKey === selectedOption.key;

            const yearlyMonthlyEquivalent = plan.yearly.price / 12;

            return (
              <article
                key={plan.id}
                className={[
                  "payment-plan-card",

                  plan.popular ? "payment-plan-card-popular" : "",

                  isCurrentPlan ? "payment-plan-card-current" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {plan.popular && (
                  <div className="payment-plan-popular-badge">Popular</div>
                )}

                {isCurrentPlan && (
                  <div className="payment-plan-your-plan-badge">Your Plan</div>
                )}

                <div className="payment-plan-card-heading">
                  <div className="payment-plan-card-icon">
                    <PlanIcon size={24} />
                  </div>

                  <div>
                    <h2>{plan.name}</h2>

                    <span>Tavora {plan.name}</span>
                  </div>
                </div>

                <p className="payment-plan-card-description">
                  {plan.description}
                </p>

                <div className="payment-plan-price">
                  <strong>{formatPrice(selectedOption.price)}</strong>

                  <span>/ {billingPeriod === "monthly" ? "muaj" : "vit"}</span>
                </div>

                <div className="payment-plan-price-note">
                  {billingPeriod === "yearly" ? (
                    <>
                      Vetëm{" "}
                      <strong>€{yearlyMonthlyEquivalent.toFixed(2)}</strong>
                      /muaj, faturuar vjet
                    </>
                  ) : (
                    "Faturim çdo 30 ditë"
                  )}
                </div>

                <div className="payment-plan-divider" />

                <div className="payment-plan-features">
                  {plan.features.map((feature) => (
                    <div key={feature}>
                      <span className="payment-plan-check">
                        <Check size={15} />
                      </span>

                      <span>{feature}</span>
                    </div>
                  ))}
                </div>

                <div className="payment-plan-card-actions">
                  <button
                    type="button"
                    className={
                      plan.popular
                        ? "payment-plan-button payment-plan-button-primary"
                        : "payment-plan-button"
                    }
                    onClick={() => handleChoosePlan(plan)}
                    disabled={Boolean(loadingPlanKey) || isCurrentPlan}
                  >
                    {isLoading ? (
                      <LoaderCircle
                        size={18}
                        className="payment-plan-spinner"
                      />
                    ) : isCurrentPlan ? (
                      <Check size={18} />
                    ) : (
                      <CreditCard size={18} />
                    )}

                    {isLoading
                      ? "Duke krijuar..."
                      : isCurrentPlan
                        ? "Current Plan"
                        : isSubscriptionActive
                          ? `Kalo në ${plan.name}`
                          : `Zgjidh ${plan.name}`}
                  </button>

                  {isDevelopment && hasPendingPayment && (
                    <button
                      type="button"
                      className="payment-plan-dev-button"
                      onClick={handleSimulateSuccess}
                      disabled={Boolean(loadingPlanKey)}
                    >
                      {isLoading ? (
                        <LoaderCircle
                          size={17}
                          className="payment-plan-spinner"
                        />
                      ) : (
                        <ShieldCheck size={17} />
                      )}

                      {isLoading ? "Duke procesuar..." : "Simulo pagesën (DEV)"}
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>

        <footer className="payment-plan-footer">
          <ShieldCheck size={18} />

          <span>
            Pagesat reale do të procesohen përmes Paddle. Simulimi i pagesës
            është i disponueshëm vetëm në development.
          </span>
        </footer>
      </section>
    </main>
  );
}

export default PaymentPlan;
