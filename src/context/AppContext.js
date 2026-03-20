import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import { mockData } from "../styles/mockData";

const AppContext = createContext(null);

const WORKFLOW_STATES = {
  idle: "idle",
  checking_conditions: "checking_conditions",
  validating: "validating",
  fraud_check: "fraud_check",
  approved: "approved",
  flagged: "flagged"
};

const PAYOUT_AMOUNT = 500;
const STEP_DELAY_MS = 1500;
const TRIGGER_RAIN_MM = 60;
const TRIGGER_AQI = 300;
const SAFE_MOVEMENT_SCORE = 0.7;
let logSequence = 0;

const evaluateRisk = (rain, aqi) => {
  if (rain >= TRIGGER_RAIN_MM || aqi >= TRIGGER_AQI) {
    return {
      isHighRisk: true,
      level: "High",
      severity: "high",
      status: "High Risk Detected in Your Area"
    };
  }

  if (rain >= 45 || aqi >= 200) {
    return {
      isHighRisk: false,
      level: "Medium",
      severity: "moderate",
      status: "Moderate Risk in Your Area"
    };
  }

  return {
    isHighRisk: false,
    level: "Low",
    severity: "normal",
    status: "Normal Conditions"
  };
};

const formatClockTime = () => {
  return new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });
};

const createLogEntry = (message, level = "info") => {
  return {
    id: `log-${Date.now()}-${++logSequence}`,
    level,
    message,
    time: formatClockTime()
  };
};

const baseRiskMeta = evaluateRisk(mockData.risk.rain, mockData.risk.aqi);

const defaultUser = {
  fullName: mockData.user.name,
  phone: "9876543210",
  email: "ramesh@gigshield.ai",
  age: "26",
  city: "Chennai",
  platform: "Blinkit",
  vehicleType: "Bike",
  workHours: "10",
  dailyIncome: "1000",
  weeklyIncome: String(mockData.finance.weeklyIncome),
  riskPreference: "Medium"
};

const defaultPolicy = {
  planName: "Standard Shield",
  premium: mockData.finance.premium,
  base: mockData.premiumBreakdown.base,
  riskAdjustment: mockData.premiumBreakdown.riskAdjustment,
  eventFactor: mockData.premiumBreakdown.eventFactor,
  coverageLeft: mockData.coverage.coverageLeft,
  weeklyCoverage: mockData.coverage.maxCoverage,
  dailyPayout: mockData.coverage.dailyCoverage,
  renewalIn: "3 days"
};

const defaultRisk = {
  aqi: mockData.risk.aqi,
  isHighRisk: baseRiskMeta.isHighRisk,
  level: baseRiskMeta.level,
  rain: mockData.risk.rain,
  severity: baseRiskMeta.severity,
  status: baseRiskMeta.status,
  temp: mockData.risk.temp
};

const buildInitialLogs = () => {
  return [
    createLogEntry("High rainfall detected", "warning"),
    createLogEntry("High AQI detected", "warning"),
    createLogEntry("Monitoring live conditions", "info")
  ];
};

const buildTimestamp = () => {
  return new Date().toLocaleString("en-IN", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short"
  });
};

export function AppProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(defaultUser);
  const [policy, setPolicy] = useState(defaultPolicy);
  const [risk, setRisk] = useState(defaultRisk);
  const [workflowState, setWorkflowState] = useState(WORKFLOW_STATES.idle);
  const [payoutAmount, setPayoutAmount] = useState(0);
  const [movementScore, setMovementScore] = useState(SAFE_MOVEMENT_SCORE);
  const [eventLogs, setEventLogs] = useState(buildInitialLogs());
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [themeEnabled, setThemeEnabled] = useState(false);
  const [claimsHistory, setClaimsHistory] = useState([]);

  const workflowRef = useRef(WORKFLOW_STATES.idle);
  const timeoutIdsRef = useRef([]);

  const clearQueuedTimeouts = useCallback(() => {
    timeoutIdsRef.current.forEach((timeoutId) => {
      clearTimeout(timeoutId);
    });
    timeoutIdsRef.current = [];
  }, []);

  const queueTimeout = useCallback((callback, delay) => {
    const timeoutId = setTimeout(() => {
      timeoutIdsRef.current = timeoutIdsRef.current.filter((item) => item !== timeoutId);
      callback();
    }, delay);

    timeoutIdsRef.current.push(timeoutId);
  }, []);

  const appendLog = useCallback((message, level = "info") => {
    setEventLogs((prev) => {
      return [createLogEntry(message, level), ...prev].slice(0, 30);
    });
  }, []);

  const resetRuntimeState = useCallback(() => {
    clearQueuedTimeouts();
    workflowRef.current = WORKFLOW_STATES.idle;

    setRisk(defaultRisk);
    setWorkflowState(WORKFLOW_STATES.idle);
    setPayoutAmount(0);
    setMovementScore(SAFE_MOVEMENT_SCORE);
    setEventLogs(buildInitialLogs());
    setClaimsHistory([]);
  }, [clearQueuedTimeouts]);

  useEffect(() => {
    workflowRef.current = workflowState;
  }, [workflowState]);

  useEffect(() => {
    return () => {
      clearQueuedTimeouts();
    };
  }, [clearQueuedTimeouts]);

  const login = ({ identifier }) => {
    resetRuntimeState();

    if (identifier?.includes("@")) {
      setUser((prev) => ({ ...prev, email: identifier }));
    } else if (identifier) {
      setUser((prev) => ({ ...prev, phone: identifier }));
    }

    setIsAuthenticated(true);
  };

  const register = (payload) => {
    setUser((prev) => ({
      ...prev,
      fullName: payload.fullName || prev.fullName,
      phone: payload.phone || prev.phone
    }));
  };

  const completeOnboarding = (payload) => {
    resetRuntimeState();

    const dailyIncome = Number(payload.dailyIncome || user.dailyIncome || 0);
    const weeklyIncome = payload.weeklyIncome
      ? Number(payload.weeklyIncome)
      : dailyIncome > 0
        ? dailyIncome * 7
        : Number(user.weeklyIncome);

    setUser((prev) => ({
      ...prev,
      fullName: payload.fullName || prev.fullName,
      age: payload.age || prev.age,
      city: payload.city || prev.city,
      platform: payload.platform || prev.platform,
      vehicleType: payload.vehicleType || prev.vehicleType,
      workHours: payload.workHours || prev.workHours,
      dailyIncome: String(dailyIncome || prev.dailyIncome),
      weeklyIncome: String(weeklyIncome || prev.weeklyIncome),
      riskPreference: payload.riskPreference || prev.riskPreference
    }));

    setPolicy((prev) => ({
      ...prev,
      premium: mockData.finance.premium,
      planName: payload.riskPreference === "High" ? "Elite Shield" : "Standard Shield"
    }));

    setIsAuthenticated(true);
  };

  const updateProfile = (payload) => {
    setUser((prev) => ({ ...prev, ...payload }));
  };

  const logout = () => {
    resetRuntimeState();
    setIsAuthenticated(false);
  };

  const startCoverageCheck = useCallback(() => {
    if (
      workflowRef.current === WORKFLOW_STATES.checking_conditions ||
      workflowRef.current === WORKFLOW_STATES.validating ||
      workflowRef.current === WORKFLOW_STATES.fraud_check
    ) {
      return;
    }

    appendLog("User requested coverage check", "info");
    setPayoutAmount(0);
    setWorkflowState(WORKFLOW_STATES.checking_conditions);
    appendLog("Checking conditions...", "warning");

    queueTimeout(() => {
      const disruptionDetected = risk.rain >= TRIGGER_RAIN_MM || risk.aqi >= TRIGGER_AQI;

      if (!disruptionDetected) {
        setWorkflowState(WORKFLOW_STATES.idle);
        appendLog("No disruption. Coverage check closed", "info");
        return;
      }

      setWorkflowState(WORKFLOW_STATES.validating);
      appendLog("Validating eligibility...", "warning");

      queueTimeout(() => {
        appendLog("Eligibility validated", "success");
        setWorkflowState(WORKFLOW_STATES.fraud_check);
        appendLog("Running fraud detection...", "warning");

        queueTimeout(() => {
          const timestamp = buildTimestamp();

          if (movementScore < 0.3) {
            setWorkflowState(WORKFLOW_STATES.flagged);
            setPayoutAmount(0);
            appendLog("Verification required", "danger");

            setClaimsHistory((prev) => {
              return [
                {
                  amount: 0,
                  event: "Parametric disruption",
                  id: `claim-${Date.now()}`,
                  status: "Flagged",
                  timestamp
                },
                ...prev
              ].slice(0, 20);
            });

            return;
          }

          setWorkflowState(WORKFLOW_STATES.approved);
          setPayoutAmount(PAYOUT_AMOUNT);
          appendLog("Fraud check passed", "success");
          appendLog(`₹${PAYOUT_AMOUNT} credited`, "success");

          setClaimsHistory((prev) => {
            return [
              {
                amount: PAYOUT_AMOUNT,
                event: "Parametric disruption",
                id: `claim-${Date.now()}`,
                status: "Approved",
                timestamp
              },
              ...prev
            ].slice(0, 20);
          });

          setPolicy((prev) => ({
            ...prev,
            coverageLeft: Math.max(0, prev.coverageLeft - PAYOUT_AMOUNT)
          }));
        }, STEP_DELAY_MS);
      }, STEP_DELAY_MS);
    }, STEP_DELAY_MS);
  }, [appendLog, movementScore, queueTimeout, risk.aqi, risk.rain]);

  const value = useMemo(
    () => ({
      isAuthenticated,
      user,
      policy,
      risk,
      workflowState,
      payoutAmount,
      movementScore,
      eventLogs,
      notificationsEnabled,
      themeEnabled,
      claimsHistory,
      login,
      register,
      completeOnboarding,
      updateProfile,
      logout,
      startCoverageCheck,
      setNotificationsEnabled,
      setThemeEnabled
    }),
    [
      isAuthenticated,
      user,
      policy,
      risk,
      workflowState,
      payoutAmount,
      movementScore,
      eventLogs,
      notificationsEnabled,
      themeEnabled,
      claimsHistory,
      startCoverageCheck
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
