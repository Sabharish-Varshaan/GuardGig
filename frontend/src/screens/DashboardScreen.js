import React, { memo } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Switch, Text, View, useWindowDimensions } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function SummaryStat({ label, value }) {
  return (
    <View style={styles.summaryStat}>
      <Text style={styles.summaryStatLabel}>{label}</Text>
      <Text style={styles.summaryStatValue}>{value}</Text>
    </View>
  );
}

function KeyValueRow({ label, value }) {
  return (
    <View style={styles.keyValueRow}>
      <Text style={styles.keyValueLabel}>{label}</Text>
      <Text style={styles.keyValueValue}>{value}</Text>
    </View>
  );
}

function formatRupee(value) {
  const amount = Number(value || 0);
  return `₹${amount.toLocaleString("en-IN")}`;
}

function formatDateTime(value) {
  if (!value) {
    return "--";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function getPolicyState(policy) {
  if (!policy) {
    return {
      isExpired: false,
      label: "INACTIVE",
      note: "Activate policy to stay protected",
      variant: "danger"
    };
  }

  const status = String(policy.status || "inactive").toLowerCase();
  const paymentStatus = String(policy.paymentStatus || "pending").toLowerCase();
  const expiresAt = policy.expiresAt ? new Date(policy.expiresAt).getTime() : null;
  const isExpired = expiresAt !== null && !Number.isNaN(expiresAt) && Date.now() > expiresAt;

  if (isExpired) {
    return {
      isExpired: true,
      label: "EXPIRED",
      note: "Renew policy to stay protected",
      variant: "info"
    };
  }

  if (status === "active" && paymentStatus === "success") {
    return {
      isExpired: false,
      label: "ACTIVE",
      note: "Coverage is live",
      variant: "success"
    };
  }

  return {
    isExpired: false,
    label: "INACTIVE",
    note: "Activate policy to stay protected",
    variant: "danger"
  };
}

function getSeverityLabel(severity) {
  const normalized = String(severity || "moderate").toLowerCase();

  if (normalized === "extreme") {
    return "Extreme";
  }

  if (normalized === "high") {
    return "High";
  }

  return "Moderate";
}

function getTriggerLabel(item) {
  if (item.triggerLabel) {
    return item.triggerLabel;
  }

  return item.triggerType === "aqi" ? "AQI" : "Rain";
}

function getPillColor(policyState) {
  if (policyState.variant === "success") {
    return appTheme.colors.successSoft;
  }

  if (policyState.variant === "info") {
    return appTheme.colors.warningSoft;
  }

  return appTheme.colors.dangerSoft;
}

function DashboardScreen() {
  const {
    user,
    policy,
    policyLoading,
    riskLoading,
    riskMessage,
    claimsHistory,
    claimsLoading,
    demoMode,
    setDemoModeEnabled,
    lastRiskCheckAt,
    dataError,
    refreshPolicy,
    refreshClaims,
    refreshRisk,
    payPremium,
    paymentLoading,
    paymentError,
    paymentMessage,
    paymentOutcome
  } = useAppContext();
  const { width } = useWindowDimensions();
  const tabBarHeight = useBottomTabBarHeight();
  const isMobileLayout = width < 768;
  const isCompactScreen = width < 390;
  const policyState = getPolicyState(policy);
  const recentPayouts = claimsHistory.slice(0, 5);
  const needsActivation = policyState.label !== "ACTIVE";

  useFocusEffect(
    React.useCallback(() => {
      let active = true;

      const syncLiveSnapshot = async () => {
        await Promise.allSettled([refreshPolicy(), refreshClaims(), refreshRisk()]);
        return active;
      };

      syncLiveSnapshot().catch(() => {});

      return () => {
        active = false;
      };
    }, [refreshClaims, refreshPolicy, refreshRisk])
  );

  const premiumValue = policy ? formatRupee(policy.premium) : "Loading...";
  const meanIncomeValue = policy ? `${formatRupee(policy.meanIncome)}/day` : "Loading...";
  const coverageValue = policy ? `${formatRupee(policy.coverageAmount)}/day` : "Loading...";
  const activatedAtValue = policy ? formatDateTime(policy.activatedAt) : "Loading...";
  const expiresAtValue = policy ? formatDateTime(policy.expiresAt) : "Loading...";
  const monitoringMessage = riskLoading ? "Monitoring environmental conditions..." : "System Status: Monitoring environmental conditions...";
  const buttonLabel = policyState.isExpired ? "Renew Policy" : "Activate Policy";
  const contentWidthStyle = {
    alignSelf: "center",
    maxWidth: width >= 1200 ? 980 : width >= 768 ? 760 : undefined,
    width: "100%"
  };
  const contentSpacingStyle = {
    paddingBottom: tabBarHeight + 20,
    paddingHorizontal: isMobileLayout ? 14 : 20,
    paddingTop: isMobileLayout ? 14 : 20
  };

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={[styles.content, contentSpacingStyle, contentWidthStyle]} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Fully automated income protection"
          title={`Hello, ${user.fullName || "Worker"} 👋`}
          rightElement={<StatusBadge label={policyState.label} variant={policyState.variant} />}
        />

        <Card gradient style={styles.sectionCard}>
          <Text style={styles.heroCaption}>Policy Status</Text>
          <View style={styles.policyHeaderRow}>
            <View style={styles.policyHeaderBlock}>
              <Text style={styles.heroLabel}>{policyState.label}</Text>
              <Text style={styles.policyNote}>{policyState.note}</Text>
            </View>
            <View style={[styles.policyPill, { backgroundColor: getPillColor(policyState) }]}>
              <Text style={styles.policyPillText}>{policyState.label}</Text>
            </View>
          </View>
          <View style={[styles.summaryStatsRow, isCompactScreen ? styles.summaryStatsRowCompact : null]}>
            <SummaryStat label="Activated At" value={activatedAtValue} />
            <SummaryStat label="Expires At" value={expiresAtValue} />
          </View>
          {policyState.isExpired && <Text style={styles.renewalHint}>Renew policy to stay protected</Text>}
        </Card>

        <Card style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Coverage & Income</Text>
            <StatusBadge label={policyState.label === "ACTIVE" ? "Protected" : "Not active"} variant={policyState.label === "ACTIVE" ? "success" : "warning"} />
          </View>
          <View style={[styles.summaryStatsRow, isCompactScreen ? styles.summaryStatsRowCompact : null]}>
            <SummaryStat label="Daily Income" value={meanIncomeValue} />
            <SummaryStat label="Coverage Amount" value={coverageValue} />
          </View>
          <SummaryStat label="Weekly Premium" value={policy ? `${premiumValue}/week` : "Loading..."} />
          <Text style={styles.coverageNote}>Coverage is based on your average daily income</Text>
        </Card>

        <Card style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Automation</Text>
            <StatusBadge label={demoMode ? "Demo Mode" : "Live"} variant={demoMode ? "warning" : "info"} />
          </View>
          <Text style={styles.automationText}>✔ Payouts are automatically triggered when disruptions occur. No manual claims needed.</Text>
          <View style={styles.toggleRow}>
            <View style={styles.toggleCopy}>
              <Text style={styles.toggleTitle}>Demo Mode</Text>
              <Text style={styles.toggleSubtitle}>Simulate a rainfall or AQI payout instantly for demo recordings.</Text>
            </View>
            <Switch
              onValueChange={setDemoModeEnabled}
              trackColor={{ false: appTheme.colors.switchTrackOff, true: appTheme.colors.switchTrackOn }}
              thumbColor={demoMode ? appTheme.colors.accentSuccess : appTheme.colors.switchThumbOff}
              value={demoMode}
            />
          </View>
          {!!paymentMessage && <Text style={paymentOutcome === "success" ? styles.paymentSuccess : styles.paymentHint}>{paymentMessage}</Text>}
          {!!paymentError && <Text style={styles.paymentError}>{paymentError}</Text>}
        </Card>

        <Card style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>System Status</Text>
            <StatusBadge label={riskLoading ? "Monitoring" : "Stable"} variant={riskLoading ? "warning" : "success"} />
          </View>
          <Text style={styles.statusText}>{monitoringMessage}</Text>
          <Text style={styles.statusMeta}>{lastRiskCheckAt ? `Last check: ${formatDateTime(lastRiskCheckAt)}` : "Last check: pending"}</Text>
          {!!riskMessage && <Text style={styles.statusMeta}>{riskMessage}</Text>}
          {(policyLoading || claimsLoading || riskLoading) && (
            <View style={styles.loadingRow}>
              <ActivityIndicator color={appTheme.colors.accentPrimary} />
              <Text style={styles.loadingText}>Syncing policy and payout data...</Text>
            </View>
          )}
          {!!dataError && <Text style={styles.errorText}>{dataError}</Text>}
        </Card>

        {needsActivation && (
          <Card style={styles.sectionCard}>
            <Text style={styles.sectionTitle}>Policy Payment</Text>
            <Text style={styles.paymentCopy}>{policyState.isExpired ? "Your policy has expired. Renew coverage to keep protection active." : "Activate policy to begin automatic protection."}</Text>
            <Button
              loading={paymentLoading}
              onPress={async () => {
                await payPremium();
                await refreshPolicy();
              }}
              style={styles.payButton}
              title={buttonLabel}
            />
            {!!paymentError && <Text style={styles.paymentError}>{paymentError}</Text>}
          </Card>
        )}

        <Card style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recent Payouts</Text>
            <StatusBadge label={recentPayouts.length > 0 ? `${recentPayouts.length} recorded` : "Empty"} variant={recentPayouts.length > 0 ? "success" : "info"} />
          </View>
          {recentPayouts.length === 0 ? (
            <Text style={styles.emptyText}>No payouts yet. You are protected when disruptions occur.</Text>
          ) : (
            recentPayouts.map((item) => (
              <View key={String(item.id)} style={styles.payoutItem}>
                <View style={styles.payoutTopRow}>
                  <Text style={styles.payoutTitle} numberOfLines={1}>
                    {`${getTriggerLabel(item)} (${getSeverityLabel(item.severity)})`}
                  </Text>
                  <Text style={styles.payoutAmount}>{formatRupee(item.amount)} credited</Text>
                </View>
                <View style={styles.payoutMetaGrid}>
                  <KeyValueRow label="Date" value={formatDateTime(item.paidAt || item.createdAt)} />
                  <KeyValueRow label="Trigger" value={getTriggerLabel(item)} />
                  <KeyValueRow label="Severity" value={getSeverityLabel(item.severity)} />
                  <KeyValueRow label="Payout %" value={item.payoutPercentage ? `${item.payoutPercentage}%` : "--"} />
                  <KeyValueRow label="Amount" value={formatRupee(item.amount)} />
                </View>
                {!!item.reason && <Text style={styles.payoutReason}>{item.reason}</Text>}
              </View>
            ))
          )}
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

export default memo(DashboardScreen);

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  content: {
    flexGrow: 1
  },
  sectionCard: {
    marginBottom: appTheme.spacing.md
  },
  heroCaption: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  policyHeaderRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: appTheme.spacing.sm
  },
  policyHeaderBlock: {
    flex: 1,
    paddingRight: appTheme.spacing.md
  },
  heroLabel: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 24,
    letterSpacing: 0.3
  },
  policyNote: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 20,
    marginTop: 4
  },
  policyPill: {
    alignItems: "center",
    borderRadius: appTheme.radius.pill,
    paddingHorizontal: 12,
    paddingVertical: 8
  },
  policyPillText: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 0.8,
    textTransform: "uppercase"
  },
  summaryStatsRow: {
    flexDirection: "row",
    gap: appTheme.spacing.sm,
    marginTop: appTheme.spacing.md
  },
  summaryStatsRowCompact: {
    flexDirection: "column"
  },
  summaryStat: {
    flex: 1
  },
  summaryStatLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 11,
    letterSpacing: 0.4,
    textTransform: "uppercase"
  },
  summaryStatValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 22,
    marginTop: appTheme.spacing.xs
  },
  renewalHint: {
    color: appTheme.colors.warningText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginTop: appTheme.spacing.sm
  },
  sectionHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.sm
  },
  sectionTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 17
  },
  coverageNote: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 20,
    marginTop: appTheme.spacing.sm
  },
  automationText: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15,
    lineHeight: 22
  },
  toggleRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: appTheme.spacing.md
  },
  toggleCopy: {
    flex: 1,
    paddingRight: appTheme.spacing.sm
  },
  toggleTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 15
  },
  toggleSubtitle: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 13,
    lineHeight: 18,
    marginTop: 2
  },
  statusText: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15,
    lineHeight: 22
  },
  statusMeta: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 13,
    marginTop: appTheme.spacing.xs
  },
  loadingRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    marginTop: appTheme.spacing.sm
  },
  loadingText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13
  },
  errorText: {
    color: appTheme.colors.dangerText,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13,
    marginTop: appTheme.spacing.sm
  },
  paymentCopy: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 20,
    marginTop: appTheme.spacing.xs
  },
  paymentHint: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: appTheme.spacing.xs
  },
  paymentError: {
    color: appTheme.colors.dangerText,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13,
    marginTop: appTheme.spacing.xs
  },
  paymentSuccess: {
    color: appTheme.colors.success,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 13,
    marginTop: appTheme.spacing.xs
  },
  payButton: {
    marginTop: appTheme.spacing.sm
  },
  emptyText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 20
  },
  payoutItem: {
    borderColor: appTheme.colors.borderSoft,
    borderTopWidth: 1,
    marginTop: appTheme.spacing.sm,
    paddingTop: appTheme.spacing.sm
  },
  payoutTopRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12
  },
  payoutTitle: {
    color: appTheme.colors.textPrimary,
    flex: 1,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 16,
    lineHeight: 22
  },
  payoutAmount: {
    color: appTheme.colors.accentSuccess,
    fontFamily: "Orbitron_700Bold",
    fontSize: 15,
    textAlign: "right"
  },
  payoutMetaGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    marginTop: appTheme.spacing.sm
  },
  keyValueRow: {
    minWidth: "44%"
  },
  keyValueLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 11,
    letterSpacing: 0.6,
    textTransform: "uppercase"
  },
  keyValueValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: 2
  },
  payoutReason: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 13,
    lineHeight: 18,
    marginTop: appTheme.spacing.sm
  }
});