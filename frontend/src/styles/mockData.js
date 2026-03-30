export const mockData = {
  user: {
    name: "Ramesh"
  },
  finance: {
    weeklyIncome: 7000,
    premium: 56,
    premiumPer: "week"
  },
  risk: {
    level: "Medium",
    status: "Partial Disruption",
    rain: 75,
    aqi: 320,
    temp: 38
  },
  coverage: {
    activePlan: "Standard Shield",
    coverageLeft: 2400,
    nextRenewalDays: 3,
    maxCoverage: 3000,
    dailyCoverage: 700
  },
  premiumBreakdown: {
    base: 36,
    riskAdjustment: 12,
    eventFactor: 8,
    total: 56
  },
  payout: {
    amount: 500
  }
};

export const formatRupees = (amount) => `₹${amount}`;

export const getRiskColor = (level) => {
  const value = level.toLowerCase();

  if (value === "high" || value === "severe") {
    return "danger";
  }

  if (value === "medium" || value.includes("partial")) {
    return "warning";
  }

  return "success";
};
