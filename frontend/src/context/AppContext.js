import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import * as Location from "expo-location";
import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

import {
  getOnboardingProfile,
  loginUser,
  registerUser,
  submitOnboardingProfile
} from "../services/authApi";
import {
  checkTrigger,
  createPolicy,
  createPaymentOrder,
  getMyClaims,
  getMyPolicy,
  verifyPayment
} from "../services/insuranceApi";

const AppContext = createContext(null);

const WORKFLOW_STATES = {
  idle: "idle",
  checking_conditions: "checking_conditions",
  validating: "validating",
  fraud_check: "fraud_check",
  approved: "approved",
  flagged: "flagged"
};

const STORAGE_KEYS = {
  token: "token",
  accessToken: "guardgig.accessToken",
  userId: "guardgig.userId"
};

const initialUser = {
  token: "",
  fullName: "",
  phone: "",
  age: "",
  city: "",
  platform: "",
  vehicleType: "",
  workHours: "",
  minIncome: "",
  maxIncome: "",
  meanIncome: "",
  incomeVariance: "",
  weeklyIncome: "",
  riskPreference: "Medium"
};

const initialRisk = {
  aqi: null,
  level: "SAFE",
  rain: null,
  status: "Awaiting live check",
  severity: null,
  trigger: null,
  triggerType: null
};

const initialLocation = {
  lat: null,
  lon: null,
  permission: "prompt",
  error: ""
};

const INELIGIBLE_MESSAGE = "You need 5 active days to activate coverage";

const createIneligiblePolicy = () => ({
  id: "",
  weeklyIncome: 0,
  meanIncome: 0,
  minIncome: 0,
  maxIncome: 0,
  incomeVariance: 0,
  premium: 0,
  coverageAmount: 0,
  paymentStatus: "pending",
  paymentId: "",
  activatedAt: "",
  policyStartDate: "",
  status: "inactive",
  eligibilityStatus: "ineligible",
  workerTier: "low",
  updatedAt: ""
});

const toStringValue = (value, fallback = "") => {
  if (value === null || value === undefined) {
    return fallback;
  }

  return String(value);
};

const mapProfileToUser = (profile, previousUser) => {
  if (!profile || typeof profile !== "object") {
    return previousUser;
  }

  return {
    ...previousUser,
    fullName: profile.full_name || previousUser.fullName,
    age: toStringValue(profile.age, previousUser.age),
    city: profile.city || previousUser.city,
    platform: profile.platform || previousUser.platform,
    vehicleType: profile.vehicle_type || previousUser.vehicleType,
    workHours: toStringValue(profile.work_hours, previousUser.workHours),
    minIncome: toStringValue(profile.min_income, previousUser.minIncome),
    maxIncome: toStringValue(profile.max_income, previousUser.maxIncome),
    meanIncome: toStringValue(profile.mean_income, previousUser.meanIncome),
    incomeVariance: toStringValue(profile.income_variance, previousUser.incomeVariance),
    weeklyIncome: toStringValue(profile.weekly_income, previousUser.weeklyIncome),
    riskPreference: profile.risk_preference || previousUser.riskPreference,
    phone: profile.phone || previousUser.phone
  };
};

const normalizePolicy = (policy) => {
  if (!policy) {
    return null;
  }

  return {
    id: policy.id,
    weeklyIncome: Number(policy.weekly_income || 0),
    meanIncome: Number(policy.mean_income || 0),
    minIncome: Number(policy.min_income || 0),
    maxIncome: Number(policy.max_income || 0),
    incomeVariance: Number(policy.income_variance || 0),
    premium: Number(policy.premium || 0),
    coverageAmount: Number(policy.coverage_amount || 0),
    paymentStatus: policy.payment_status || "pending",
    paymentId: policy.payment_id || "",
    activatedAt: policy.activated_at || "",
    expiresAt: policy.expires_at || "",
    policyStartDate: policy.policy_start_date || "",
    status: policy.status || "inactive",
    eligibilityStatus: policy.eligibility_status || "eligible",
    workerTier: policy.worker_tier || "medium",
    updatedAt: policy.updated_at || ""
  };
};

const normalizeClaim = (claim) => {
  const createdAt = claim?.created_at || "";
  const snapshot = claim?.trigger_snapshot && typeof claim.trigger_snapshot === "object" ? claim.trigger_snapshot : {};
  const reason = claim?.rule_decision_reason || snapshot.rule_decision_reason || "";
  const triggerType = claim?.trigger_type || snapshot.trigger_type || "rain";
  const severity = (claim?.severity || snapshot.severity || "moderate").toLowerCase();
  const payoutPercentage = Number(claim?.payout_percentage ?? snapshot.payout_percentage ?? 0);
  const triggerValue = Number(claim?.trigger_value ?? snapshot.trigger_value ?? 0);

  return {
    id: claim?.id || String(Date.now()),
    type: triggerType,
    triggerType,
    severity,
    payoutPercentage,
    status: (claim?.status || "pending").toLowerCase(),
    amount: Number(claim?.payout_amount || 0),
    triggerValue,
    triggerLabel: triggerType === "aqi" ? "AQI" : "Rain",
    paymentStatus: (claim?.payment_status || "pending").toLowerCase(),
    transactionId: claim?.transaction_id || "",
    paidAt: claim?.paid_at || "",
    payoutMethod: claim?.payout_method || "",
    reason,
    triggerSnapshot: snapshot,
    createdAt,
    timestamp: createdAt
      ? new Date(createdAt).toLocaleString("en-IN", {
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          month: "short"
        })
      : ""
  };
};

const createDemoClaim = ({ triggerType, severity, payoutPercentage, payoutAmount }) => {
  const now = new Date().toISOString();

  return normalizeClaim({
    id: `demo-${Date.now()}`,
    trigger_type: triggerType,
    severity,
    payout_amount: payoutAmount,
    payout_percentage: payoutPercentage,
    trigger_value: triggerType === "aqi" ? 420 : 88,
    status: "approved",
    payment_status: "paid",
    transaction_id: `demo-${triggerType}-${Date.now()}`,
    paid_at: now,
    payout_method: "demo",
    created_at: now,
    trigger_snapshot: {
      trigger_type: triggerType,
      severity,
      payout_percentage: payoutPercentage,
      payout_amount: payoutAmount,
      trigger_value: triggerType === "aqi" ? 420 : 88,
      rule_decision_reason: `demo_mode_${triggerType}_${severity}`
    },
    rule_decision_reason: `demo_mode_${triggerType}_${severity}`
  });
};

const resolveRiskLevel = (severity) => {
  if (severity === "extreme") {
    return "HIGH";
  }

  if (severity === "high" || severity === "moderate") {
    return "MODERATE";
  }

  return "SAFE";
};

const toErrorMessage = (error, fallback) => {
  if (error instanceof Error) {
    return error.message;
  }

  return fallback;
};

const toBooleanFlag = (value) => {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "number") {
    return value === 1;
  }

  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();

    if (normalized === "true" || normalized === "1" || normalized === "yes") {
      return true;
    }

    if (normalized === "false" || normalized === "0" || normalized === "no" || normalized === "") {
      return false;
    }
  }

  return Boolean(value);
};

const getSecureItem = async (key) => {
  if (typeof SecureStore?.getItemAsync !== "function") {
    return null;
  }

  try {
    return await SecureStore.getItemAsync(key);
  } catch (_error) {
    return null;
  }
};

const setSecureItem = async (key, value) => {
  if (typeof SecureStore?.setItemAsync !== "function") {
    return;
  }

  try {
    await SecureStore.setItemAsync(key, value);
  } catch (_error) {
    // SecureStore can be unavailable on some web runtimes.
  }
};

const deleteSecureItem = async (key) => {
  if (typeof SecureStore?.deleteItemAsync !== "function") {
    return;
  }

  try {
    await SecureStore.deleteItemAsync(key);
  } catch (_error) {
    // SecureStore can be unavailable on some web runtimes.
  }
};

export function AppProvider({ children }) {
  const [authInitializing, setAuthInitializing] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authToken, setAuthToken] = useState("");
  const [authUserId, setAuthUserId] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [dataError, setDataError] = useState("");
  const [pendingOnboardingUser, setPendingOnboardingUser] = useState(null);
  const [user, setUser] = useState(initialUser);
  const [policy, setPolicy] = useState(null);
  const [policyLoading, setPolicyLoading] = useState(false);
  const [claimsHistory, setClaimsHistory] = useState([]);
  const [claimsLoading, setClaimsLoading] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [demoClaimsHistory, setDemoClaimsHistory] = useState([]);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentError, setPaymentError] = useState("");
  const [paymentMessage, setPaymentMessage] = useState("");
  const [paymentOutcome, setPaymentOutcome] = useState("idle");
  const [risk, setRisk] = useState(initialRisk);
  const [location, setLocation] = useState(initialLocation);
  const locationRef = useRef(initialLocation);
  const [riskLoading, setRiskLoading] = useState(false);
  const [riskMessage, setRiskMessage] = useState("Awaiting live check");
  const [workflowState, setWorkflowState] = useState(WORKFLOW_STATES.idle);
  const [workflowMessage, setWorkflowMessage] = useState("No active claim check");
  const [coverageLoading, setCoverageLoading] = useState(false);
  const [payoutAmount, setPayoutAmount] = useState(0);
  const [lastRiskCheckAt, setLastRiskCheckAt] = useState("");
  const [movementScore] = useState(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [themeEnabled, setThemeEnabled] = useState(false);

  // Keep location ref in sync with location state to avoid circular dependencies
  useEffect(() => {
    locationRef.current = location;
  }, [location]);

  const applyAuthSession = useCallback((session) => {
    setAuthToken(session.access_token || "");
    setAuthUserId(session.user_id || "");
  }, []);

  const clearAuthState = useCallback(() => {
    setAuthToken("");
    setAuthUserId("");
    setAuthError("");
    setDataError("");
    setPaymentError("");
    setPendingOnboardingUser(null);
    setAuthLoading(false);
  }, []);

  const persistSession = useCallback(async (session) => {
    const accessToken = session?.access_token || "";
    const userId = session?.user_id || "";

    if (!accessToken || !userId) {
      await AsyncStorage.removeItem(STORAGE_KEYS.token);
      await deleteSecureItem(STORAGE_KEYS.accessToken);
      await deleteSecureItem(STORAGE_KEYS.userId);
      return;
    }

    await AsyncStorage.setItem(STORAGE_KEYS.token, accessToken);
    await setSecureItem(STORAGE_KEYS.accessToken, accessToken);
    await setSecureItem(STORAGE_KEYS.userId, userId);
  }, []);

  const clearPersistedSession = useCallback(async () => {
    await AsyncStorage.removeItem(STORAGE_KEYS.token);
    await deleteSecureItem(STORAGE_KEYS.accessToken);
    await deleteSecureItem(STORAGE_KEYS.userId);
  }, []);

  const hydrateFromProfile = useCallback((profile) => {
    setUser((prev) => mapProfileToUser(profile, prev));
  }, []);

  const refreshPolicy = useCallback(
    async (tokenOverride) => {
      const token = tokenOverride || authToken;

      if (!token) {
        return null;
      }

      setPolicyLoading(true);
      setDataError("");
      setPaymentError("");

      try {
        const response = await getMyPolicy(token);
        const normalized = normalizePolicy(response);
        setPolicy(normalized);
        return normalized;
      } catch (error) {
        const message = toErrorMessage(error, "Unable to fetch policy");

        if (message.toLowerCase().includes("no policy found")) {
          setPolicy(null);
          return null;
        }

        setDataError(message);
        throw error;
      } finally {
        setPolicyLoading(false);
      }
    },
    [authToken]
  );

  const createPolicyForCurrentUser = useCallback(
    async (tokenOverride) => {
      const token = tokenOverride || authToken;

      if (!token) {
        throw new Error("Session expired. Please login again.");
      }

      setPolicyLoading(true);
      setDataError("");

      try {
        const response = await createPolicy(token);

        if (response?.status === "ineligible") {
          const ineligiblePolicy = createIneligiblePolicy();
          setPolicy(ineligiblePolicy);
          return ineligiblePolicy;
        }

        const normalized = normalizePolicy(response?.policy);
        setPolicy(normalized);
        return normalized;
      } catch (error) {
        const message = toErrorMessage(error, "Policy creation failed");

        if (message.toLowerCase().includes("policy already exists")) {
          return refreshPolicy(token);
        }

        setDataError(message);
        throw error;
      } finally {
        setPolicyLoading(false);
      }
    },
    [authToken, refreshPolicy]
  );

  const refreshClaims = useCallback(
    async (tokenOverride) => {
      const token = tokenOverride || authToken;

      if (!token) {
        return [];
      }

      setClaimsLoading(true);
      setDataError("");

      try {
        const response = await getMyClaims(token);
        const claims = Array.isArray(response?.claims) ? response.claims.map(normalizeClaim) : [];
        setClaimsHistory(claims);

        if (claims.length > 0) {
          setPayoutAmount(claims[0].amount || 0);
        }

        return claims;
      } catch (error) {
        setDataError(toErrorMessage(error, "Unable to fetch claims"));
        throw error;
      } finally {
        setClaimsLoading(false);
      }
    },
    [authToken]
  );

  const setDemoModeEnabled = useCallback(
    (enabled) => {
      const nextEnabled = Boolean(enabled);
      setDemoMode(nextEnabled);

      if (!nextEnabled) {
        setDemoClaimsHistory([]);
        setWorkflowState(WORKFLOW_STATES.idle);
        setWorkflowMessage("No active automated payout");
        setPaymentMessage("");
        setPaymentError("");
        return;
      }

      const triggerType = risk.triggerType === "aqi" ? "aqi" : "rain";
      const severity = (risk.severity || (triggerType === "aqi" ? "high" : "high")).toLowerCase();
      const coverageBase = Number(policy?.meanIncome || user.meanIncome || 0);
      const coverageLimit = Number(policy?.coverageAmount || 0);
      const payoutPercentage = triggerType === "aqi" ? 100 : severity === "high" ? 60 : 30;
      const payoutBase = coverageBase > 0 ? Math.min(coverageBase, coverageLimit > 0 ? coverageLimit : coverageBase) : 300;
      const payoutAmountValue = Math.max(300, Math.round((payoutPercentage / 100) * payoutBase));
      const demoClaim = createDemoClaim({
        triggerType,
        severity,
        payoutPercentage,
        payoutAmount: payoutAmountValue
      });

      setDemoClaimsHistory([demoClaim]);
      setWorkflowState(WORKFLOW_STATES.approved);
      setWorkflowMessage("Demo payout simulated");
      setPayoutAmount(demoClaim.amount);
      setPaymentOutcome("success");
      setPaymentMessage("Demo payout credited instantly");
      setPaymentError("");
      setRiskMessage(triggerType === "aqi" ? "Demo AQI disruption" : "Demo rainfall disruption");
      setLastRiskCheckAt(new Date().toISOString());
    },
    [policy?.coverageAmount, policy?.meanIncome, risk.severity, risk.triggerType, user.meanIncome]
  );

  const requestLocation = useCallback(async () => {
    try {
      const permission = await Location.requestForegroundPermissionsAsync();
      if (permission.status !== "granted") {
        setLocation((prev) => ({
          ...prev,
          permission: "denied",
          error: "Location permission denied"
        }));
        return null;
      }

      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced
      });

      const next = {
        lat: Number(position.coords.latitude),
        lon: Number(position.coords.longitude),
        permission: "granted",
        error: ""
      };

      setLocation(next);
      return next;
    } catch (error) {
      const message = toErrorMessage(error, "Unable to fetch location");
      setLocation((prev) => ({
        ...prev,
        permission: "denied",
        error: message
      }));
      return null;
    }
  }, []);

  const refreshRisk = useCallback(async (locationOverride) => {
    setRiskLoading(true);
    setDataError("");
    setPaymentError("");

    try {
      const resolvedLocation = locationOverride || (locationRef.current.lat !== null && locationRef.current.lon !== null ? locationRef.current : await requestLocation());

      if (!resolvedLocation || resolvedLocation.lat === null || resolvedLocation.lon === null) {
        setRiskMessage(locationRef.current.error || "Location permission required");
        return null;
      }

      const triggerResponse = await checkTrigger({
        lat: resolvedLocation.lat,
        lon: resolvedLocation.lon
      });
      const rain = Number(triggerResponse?.rain ?? 0);
      const aqi = Number(triggerResponse?.aqi ?? 0);
      const severity = triggerResponse?.severity || null;
      const triggerType = triggerResponse?.trigger_type || null;
      const detected = !!triggerType;

      // Determine final status message based on trigger type
      let finalStatusMessage = "No disruption detected";
      if (triggerType === "rain") {
        finalStatusMessage = "Heavy rain detected";
      } else if (triggerType === "aqi") {
        finalStatusMessage = "Air quality unsafe";
      }

      // Batch all state updates together to avoid multiple re-renders
      setRisk({
        rain,
        aqi,
        level: resolveRiskLevel(severity),
        status:
          triggerType === "rain"
            ? "Heavy rain detected"
            : triggerType === "aqi"
              ? "Air quality unsafe"
              : "Safe conditions",
        severity,
        trigger: detected,
        triggerType
      });

      // Single state update for message after risk data is set
      setRiskMessage(finalStatusMessage);
      setLastRiskCheckAt(new Date().toISOString());

      return {
        trigger: {
          trigger: detected,
          type: triggerType,
          severity
        },
        detected,
        rain,
        aqi,
        lat: resolvedLocation.lat,
        lon: resolvedLocation.lon
      };
    } catch (error) {
      const message = toErrorMessage(error, "Failed to check trigger");
      setRiskMessage(message);
      setDataError(message);
      throw error;
    } finally {
      setRiskLoading(false);
    }
  }, [requestLocation]);

  useEffect(() => {
    let mounted = true;

    const restoreSession = async () => {
      setAuthInitializing(true);

      try {
        const [secureAccessToken, secureUserId, asyncToken] = await Promise.all([
          getSecureItem(STORAGE_KEYS.accessToken),
          getSecureItem(STORAGE_KEYS.userId),
          AsyncStorage.getItem(STORAGE_KEYS.token)
        ]);
        const accessToken = secureAccessToken || asyncToken || "";
        const userId = secureUserId || "";

        if (!accessToken) {
          if (mounted) {
            setAuthInitializing(false);
          }
          return;
        }

        if (mounted) {
          setAuthToken(accessToken);
          setAuthUserId(userId);
          setUser((prev) => ({ ...prev, token: accessToken }));
        }

        const onboardingData = await getOnboardingProfile(accessToken);
        const hasOnboarded = toBooleanFlag(onboardingData?.onboarding_completed);

        if (!mounted) {
          return;
        }

        if (hasOnboarded) {
          hydrateFromProfile(onboardingData.profile || {});
          setPendingOnboardingUser(null);
          setIsAuthenticated(true);
          await Promise.allSettled([
            refreshPolicy(accessToken),
            refreshClaims(accessToken)
          ]);
        } else {
          setPendingOnboardingUser({
            phone: initialUser.phone,
            fullName: initialUser.fullName
          });
          setIsAuthenticated(false);
        }
      } catch (_error) {
        if (!mounted) {
          return;
        }

        clearAuthState();
        setIsAuthenticated(false);
        await clearPersistedSession();
      } finally {
        if (mounted) {
          setAuthInitializing(false);
        }
      }
    };

    restoreSession();

    return () => {
      mounted = false;
    };
  }, []);

  const register = async (payload) => {
    setAuthLoading(true);
    setAuthError("");

    try {
      const session = await registerUser(payload);

      applyAuthSession(session);
      await persistSession(session);
      setPendingOnboardingUser({
        fullName: payload.fullName,
        phone: payload.phone
      });

      setUser((prev) => ({
        ...prev,
        fullName: payload.fullName || prev.fullName,
        phone: payload.phone || prev.phone
      }));

      return { success: true };
    } catch (error) {
      const message = toErrorMessage(error, "Registration failed");
      setAuthError(message);
      return { success: false, error: message };
    } finally {
      setAuthLoading(false);
    }
  };

  const login = async ({ phone, password }) => {
    setAuthLoading(true);
    setAuthError("");

    try {
      const session = await loginUser({ phone, password });
      const hasCompletedOnboarding = toBooleanFlag(session?.onboarding_completed);

      applyAuthSession(session);
      await persistSession(session);

      setUser((prev) => ({ ...prev, phone, token: session.access_token || "" }));

      if (hasCompletedOnboarding) {
        const onboardingData = await getOnboardingProfile(session.access_token);
        if (onboardingData?.profile) {
          hydrateFromProfile(onboardingData.profile);
        }

        await Promise.allSettled([
          refreshPolicy(session.access_token),
          refreshClaims(session.access_token)
        ]);

        setIsAuthenticated(true);
        setPendingOnboardingUser(null);
      } else {
        setIsAuthenticated(false);
        setPendingOnboardingUser((prev) => ({
          phone,
          fullName: prev?.fullName || user.fullName || ""
        }));
      }

      return {
        success: true,
        accessToken: session.access_token || "",
        onboardingCompleted: hasCompletedOnboarding
      };
    } catch (error) {
      const message = toErrorMessage(error, "Login failed");
      setAuthError(message);
      return { success: false, error: message };
    } finally {
      setAuthLoading(false);
    }
  };

  const completeOnboarding = async (payload) => {
    if (!authToken) {
      const message = "Session expired. Please login again.";
      setAuthError(message);
      return { success: false, error: message };
    }

    setAuthLoading(true);
    setAuthError("");

    try {
      const onboardingData = await submitOnboardingProfile(payload, authToken);
      const profile = onboardingData?.profile || payload;

      setUser((prev) => mapProfileToUser(profile, prev));
      await createPolicyForCurrentUser(authToken);
      await refreshClaims(authToken);

      setPendingOnboardingUser(null);
      setIsAuthenticated(true);
      setPaymentError("");
      return { success: true };
    } catch (error) {
      const message = toErrorMessage(error, "Onboarding submit failed");
      setAuthError(message);
      return { success: false, error: message };
    } finally {
      setAuthLoading(false);
    }
  };

  const updateProfile = (payload) => {
    setUser((prev) => ({ ...prev, ...payload }));
  };

  const logout = () => {
    clearAuthState();
    clearPersistedSession().catch(() => {});
    setUser(initialUser);
    setPolicy(null);
    setRisk(initialRisk);
    setLocation(initialLocation);
    setRiskMessage("Awaiting live check");
    setClaimsHistory([]);
    setDemoClaimsHistory([]);
    setPayoutAmount(0);
    setWorkflowState(WORKFLOW_STATES.idle);
    setWorkflowMessage("No active claim check");
    setDemoMode(false);
    setLastRiskCheckAt("");
    setIsAuthenticated(false);
  };

  const payPremium = useCallback(async () => {
    if (!authToken) {
      const message = "Session expired. Please login again.";
      setPaymentError(message);
      return { success: false, error: message };
    }

    if (!policy) {
      const message = "Policy not found";
      setPaymentError(message);
      return { success: false, error: message };
    }

    if ((policy.paymentStatus || "pending") === "success") {
      setPaymentOutcome("success");
      setPaymentMessage("Premium already paid");
      return { success: true, alreadyPaid: true };
    }

    if (Platform.OS !== "web") {
      const message = "Razorpay checkout is available only on PWA/browser.";
      setPaymentError(message);
      setPaymentOutcome("failure");
      setPaymentMessage("Payment failed");
      return { success: false, error: message };
    }

    const RazorpayConstructor = globalThis?.Razorpay;
    if (typeof RazorpayConstructor !== "function") {
      const message = "Razorpay checkout failed to load. Refresh and try again.";
      setPaymentError(message);
      setPaymentOutcome("failure");
      setPaymentMessage("Payment failed");
      return { success: false, error: message };
    }

    setPaymentLoading(true);
    setPaymentError("");
    setPaymentMessage("Creating payment order...");
    setPaymentOutcome("idle");

    try {
      const orderResponse = await createPaymentOrder(authToken);

      return await new Promise((resolve) => {
        let settled = false;
        const complete = (result) => {
          if (settled) {
            return;
          }

          settled = true;
          setPaymentLoading(false);
          resolve(result);
        };

        const options = {
          key: orderResponse.key_id,
          amount: Number(orderResponse.amount || 0),
          currency: orderResponse.currency || "INR",
          name: "GuardGig",
          description: "Weekly Insurance Premium",
          order_id: orderResponse.order_id,
          handler: async function (response) {
            setPaymentMessage("Verifying payment...");

            try {
              const paymentId = response?.razorpay_payment_id;
              const signature = response?.razorpay_signature;
              if (!paymentId) {
                throw new Error("Missing Razorpay payment id");
              }
              if (!signature) {
                throw new Error("Missing Razorpay signature");
              }

              await verifyPayment(authToken, {
                orderId: orderResponse.order_id,
                paymentId,
                signature
              });

              await refreshPolicy(authToken);
              setPaymentError("");
              setPaymentOutcome("success");
              setPaymentMessage("Payment successful. Policy activated.");
              complete({ success: true, orderId: orderResponse.order_id, paymentId });
            } catch (error) {
              const message = toErrorMessage(error, "Payment verification failed");
              setPaymentError(message);
              setPaymentOutcome("failure");
              setPaymentMessage("Payment failed");
              complete({ success: false, error: message });
            }
          },
          modal: {
            ondismiss: function () {
              setPaymentError("Payment was cancelled");
              setPaymentOutcome("failure");
              setPaymentMessage("Payment cancelled");
              complete({ success: false, cancelled: true, error: "Payment cancelled" });
            }
          }
        };

        try {
          const checkout = new RazorpayConstructor(options);

          checkout.on("payment.failed", (event) => {
            const message =
              event?.error?.description ||
              event?.error?.reason ||
              "Payment failed";

            setPaymentError(message);
            setPaymentOutcome("failure");
            setPaymentMessage("Payment failed");
            complete({ success: false, error: message });
          });

          setPaymentMessage("Opening Razorpay checkout...");
          checkout.open();
        } catch (error) {
          const message = toErrorMessage(error, "Unable to open Razorpay checkout");
          setPaymentError(message);
          setPaymentOutcome("failure");
          setPaymentMessage("Payment failed");
          complete({ success: false, error: message });
        }
      });
    } catch (error) {
      const message = toErrorMessage(error, "Payment failed");
      setPaymentError(message);
      setPaymentOutcome("failure");
      setPaymentMessage("Payment failed");
      return { success: false, error: message };
    }
  }, [authToken, policy, refreshPolicy]);

  const visibleClaimsHistory = useMemo(
    () => (demoMode && demoClaimsHistory.length > 0 ? [...demoClaimsHistory, ...claimsHistory] : claimsHistory),
    [claimsHistory, demoClaimsHistory, demoMode]
  );
  const visiblePayoutAmount = demoMode && demoClaimsHistory[0] ? demoClaimsHistory[0].amount : payoutAmount;

  const value = useMemo(
    () => ({
      isAuthenticated,
      authInitializing,
      authLoading,
      authError,
      dataError,
      pendingOnboardingUser,
      authToken,
      authUserId,
      user,
      policy,
      policyLoading,
      risk,
      location,
      riskLoading,
      riskMessage,
      workflowState,
      workflowMessage,
      coverageLoading,
      payoutAmount: visiblePayoutAmount,
      movementScore,
      claimsHistory: visibleClaimsHistory,
      claimsLoading,
      demoMode,
      setDemoModeEnabled,
      paymentLoading,
      paymentError,
      paymentMessage,
      paymentOutcome,
      lastRiskCheckAt,
      eligibilityMessage: INELIGIBLE_MESSAGE,
      notificationsEnabled,
      themeEnabled,
      login,
      register,
      completeOnboarding,
      updateProfile,
      logout,
      requestLocation,
      refreshRisk,
      refreshPolicy,
      refreshClaims,
      payPremium,
      activatePolicyPayment: payPremium,
      setNotificationsEnabled,
      setThemeEnabled,
      setAuthError
    }),
    [
      isAuthenticated,
      authInitializing,
      authLoading,
      authError,
      dataError,
      pendingOnboardingUser,
      authToken,
      authUserId,
      user,
      policy,
      policyLoading,
      risk,
      location,
      riskLoading,
      riskMessage,
      workflowState,
      workflowMessage,
      coverageLoading,
      visiblePayoutAmount,
      movementScore,
      visibleClaimsHistory,
      claimsLoading,
      demoMode,
      setDemoModeEnabled,
      paymentLoading,
      paymentError,
      paymentMessage,
      paymentOutcome,
      lastRiskCheckAt,
      INELIGIBLE_MESSAGE,
      notificationsEnabled,
      themeEnabled,
      requestLocation,
      refreshRisk,
      refreshPolicy,
      refreshClaims,
      payPremium
    ]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext() {
  const context = useContext(AppContext);

  if (!context) {
    throw new Error("useAppContext must be used within AppProvider");
  }

  return context;
}
