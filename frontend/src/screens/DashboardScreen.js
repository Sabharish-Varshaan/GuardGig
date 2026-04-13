import React, { memo, useMemo } from "react";
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import Button from "../components/Button";
import Header from "../components/Header";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function InfoRow({ icon, label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{`${icon} ${label}`}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

function SummaryStat({ label, value }) {
  return (
    <View style={styles.summaryStat}>
      <Text style={styles.summaryStatLabel}>{label}</Text>
      <Text style={styles.summaryStatValue}>{value}</Text>
    </View>
  );
}

function formatRupee(value) {
  return `₹${value}`;
}

function formatRelativeTime(timestamp) {
  if (!timestamp) {
    return "Just now";
  }

  const date = new Date(timestamp);
  const deltaMs = Date.now() - date.getTime();

  if (Number.isNaN(deltaMs) || deltaMs < 0) {
    return "Just now";
  }

  const minutes = Math.floor(deltaMs / 60000);
  if (minutes < 1) {
    return "Just now";
  }
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  }

  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function getVariantFromRiskLevel(level) {
  const normalized = (level || "safe").toLowerCase();

  if (normalized === "high") {
    return "danger";
  }

  if (normalized === "moderate") {
    return "warning";
  }

  return "success";
}

function resolveRiskHeadline(severity) {
  if (severity === "full") {
    return "HIGH RISK DETECTED";
  }

  if (severity === "partial") {
    return "MODERATE RISK";
  }

  return "SAFE CONDITIONS";
}

function getWorkflowStatusMeta(workflowState, workflowMessage) {
  if (workflowState === "checking_conditions") {
    return { label: "System evaluating...", variant: "info" };
  }

  if (workflowState === "validating") {
    return { label: "Claim triggered automatically", variant: "info" };
  }

  if (workflowState === "fraud_check") {
    return { label: "Processing...", variant: "warning" };
  }

  if (workflowState === "approved") {
    return { label: "Approved", variant: "success" };
  }

  if (workflowState === "flagged") {
    if ((workflowMessage || "").toLowerCase().includes("already")) {
      return { label: "Claim is already done", variant: "danger" };
    }
    return { label: "Conditions not met", variant: "danger" };
  }

  return { label: "No active claim check", variant: "info" };
}

function DashboardScreen({ navigation }) {
  const {
    user,
    policy,
    policyLoading,
    risk,
    location,
    riskLoading,
    riskMessage,
    workflowState,
    workflowMessage,
    claimsHistory,
    eligibilityMessage,
    requestLocation,
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
  const contentWidthStyle = useMemo(
    () => ({
      alignSelf: "center",
      maxWidth: width >= 1200 ? 980 : width >= 768 ? 760 : undefined,
      width: "100%"
    }),
    [width]
  );
  const contentSpacingStyle = useMemo(
    () => ({
      paddingBottom: tabBarHeight + 18,
      paddingHorizontal: isMobileLayout ? 14 : 20,
      paddingTop: isMobileLayout ? 14 : 20
    }),
    [isMobileLayout, tabBarHeight]
  );
  const policyReady = !policyLoading && !!policy;
  const isCoverageEligible =
    policyReady && policy.status === "active" && policy.eligibilityStatus === "eligible" && policy.paymentStatus === "success";
  const paymentPending = policyReady && policy.paymentStatus !== "success";

  useFocusEffect(
    React.useCallback(() => {
      let active = true;

      const syncLiveSnapshot = async () => {
        const coords = await requestLocation();
        if (!active) {
          return;
        }

        await refreshRisk(coords || undefined);
      };

      syncLiveSnapshot().catch(() => {});

      return () => {
        active = false;
      };
    }, [refreshRisk, requestLocation])
  );

  const riskVariant = useMemo(() => getVariantFromRiskLevel(risk.level), [risk.level]);
  const compactRiskLabel = useMemo(() => resolveRiskHeadline(risk.severity), [risk.severity]);
  const workflowMeta = useMemo(() => getWorkflowStatusMeta(workflowState, workflowMessage), [workflowMessage, workflowState]);
  const liveRiskLabel = riskLoading ? "CHECKING" : compactRiskLabel;
  const premiumValue = policyReady ? `${formatRupee(policy.premium)}/week` : "Loading...";
  const meanIncomeValue = policyReady ? `${formatRupee(policy.meanIncome)}/day` : "Loading...";
  const coverageValue = policyReady ? `${formatRupee(policy.coverageAmount)}/day` : "Loading...";
  const recentEvents = useMemo(() => {
    const claimEvents = claimsHistory.slice(0, 3).map((claim) => {
      const label = claim.type === "aqi" ? "AQI trigger" : "Rain trigger";
      return `${label}: ${claim.status} (${formatRelativeTime(claim.createdAt)})`;
    });

    const workflowEvent = workflowMessage ? `Workflow: ${workflowMessage}` : null;
    const riskEvent = riskMessage ? `Risk: ${riskMessage}` : null;

    return [workflowEvent, riskEvent, ...claimEvents].filter(Boolean);
  }, [claimsHistory, riskMessage, workflowMessage]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={[styles.content, contentSpacingStyle, contentWidthStyle]} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Your income is protected"
          title={`Hello, ${user.fullName || "Worker"} 👋`}
          rightElement={<StatusBadge label={liveRiskLabel} variant={riskVariant} />}
        />

        <Card gradient style={styles.summaryCard}>
          <Text style={styles.heroCaption}>Policy Snapshot</Text>
          <View style={[styles.summaryTopRow, isCompactScreen ? styles.summaryTopRowCompact : null]}>
            <View style={styles.summaryPrimaryBlock}>
              <Text style={styles.heroLabel}>Premium</Text>
              <Text style={styles.heroValue}>{premiumValue}</Text>
            </View>
            <StatusBadge
              label={paymentPending ? `Payment ${policy.paymentStatus || "pending"}` : liveRiskLabel}
              variant={paymentPending ? "warning" : riskVariant}
            />
          </View>
          <View style={[styles.summaryStatsRow, isCompactScreen ? styles.summaryStatsRowCompact : null]}>
            <SummaryStat label="Average Daily Income" value={meanIncomeValue} />
            <SummaryStat label="Daily Coverage" value={coverageValue} />
          </View>
          {paymentPending && (
            <>
              <Text style={styles.paymentHint}>Premium payment is required before claims are unlocked.</Text>
              {!!paymentError && <Text style={styles.paymentError}>{paymentError}</Text>}
              <Button
                loading={paymentLoading}
                onPress={async () => {
                  await payPremium();
                }}
                style={styles.payButton}
                title={`Pay Now • ${premiumValue}`}
              />
              {!!paymentMessage && (
                <Text style={paymentOutcome === "success" ? styles.paymentSuccess : styles.paymentHint}>{paymentMessage}</Text>
              )}
            </>
          )}
        </Card>

        <Card style={styles.liveRiskCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Live Risk Panel</Text>
            <StatusBadge label={liveRiskLabel} variant={riskVariant} />
          </View>
          <View style={[styles.liveRiskGrid, isCompactScreen ? styles.liveRiskGridCompact : null]}>
            <InfoRow icon="🌧️" label="Rain" value={risk.rain === null ? "--" : `${risk.rain} mm`} />
            <InfoRow icon="🌫️" label="AQI" value={risk.aqi === null ? "--" : `${risk.aqi}`} />
            <InfoRow icon="📍" label="Latitude" value={location.lat === null ? "--" : `${location.lat.toFixed(4)}`} />
            <InfoRow icon="📍" label="Longitude" value={location.lon === null ? "--" : `${location.lon.toFixed(4)}`} />
            <InfoRow icon="⚡" label="Risk Status" value={liveRiskLabel} />
          </View>
        </Card>

        <View style={styles.inlineStatusRow}>
          <Text style={styles.inlineStatusLabel}>Live</Text>
          <StatusBadge label={riskMessage} variant={riskLoading ? "warning" : riskVariant} />
        </View>

        {!isCoverageEligible && policyReady && (
          <Text style={styles.warningText}>{policy.paymentStatus === "success" ? eligibilityMessage : "Premium payment required"}</Text>
        )}

        <Card style={styles.messageCard}>
          <Text style={styles.messageHeading}>Automation Feed</Text>
          <Text style={styles.feedItem}>Payouts are automatic when disruption occurs.</Text>
          {recentEvents.length === 0 ? (
            <Text style={styles.feedItem}>No activity yet</Text>
          ) : (
            recentEvents.map((event) => (
              <Text key={event} style={styles.feedItem}>{event}</Text>
            ))
          )}
        </Card>

        <View style={styles.inlineStatusRow}>
          <Text style={styles.inlineStatusLabel}>Workflow</Text>
            <StatusBadge label={workflowMessage} variant={workflowMeta.variant} />
        </View>

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
  summaryCard: {
    marginBottom: appTheme.spacing.md
  },
  heroCaption: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  summaryTopRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: appTheme.spacing.sm
  },
  summaryTopRowCompact: {
    flexDirection: "column"
  },
  summaryPrimaryBlock: {
    flex: 1,
    paddingRight: appTheme.spacing.md
  },
  summaryStatsRow: {
    flexDirection: "row",
    gap: appTheme.spacing.sm,
    marginTop: appTheme.spacing.md
  },
  summaryStatsRowCompact: {
    flexDirection: "column"
  },
  paymentHint: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: appTheme.spacing.sm
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
  summaryStat: {
    flex: 1
  },
  summaryStatLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    textTransform: "uppercase"
  },
  summaryStatValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 18,
    marginTop: appTheme.spacing.xs
  },
  heroLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14
  },
  heroValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 30,
    marginTop: appTheme.spacing.xs
  },
  liveRiskCard: {
    marginBottom: appTheme.spacing.lg
  },
  sectionHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.md
  },
  sectionTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18,
    letterSpacing: 0.2
  },
  liveRiskGrid: {
    gap: appTheme.spacing.sm
  },
  liveRiskGridCompact: {
    gap: appTheme.spacing.xs
  },
  infoRow: {
    alignItems: "center",
    borderBottomColor: appTheme.colors.borderSubtle,
    borderBottomWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingBottom: appTheme.spacing.xs,
    paddingTop: appTheme.spacing.xs
  },
  infoLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14
  },
  infoValue: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 15
  },
  inlineStatusRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.md,
    marginTop: appTheme.spacing.xs
  },
  inlineStatusLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 0.8,
    textTransform: "uppercase"
  },
  messageCard: {
    marginBottom: appTheme.spacing.md
  },
  warningText: {
    color: appTheme.colors.warningText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginBottom: appTheme.spacing.md
  },
  messageHeading: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 16,
    marginBottom: appTheme.spacing.xs
  },
  feedItem: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15,
    lineHeight: 22
  },
});
