import React, { memo, useMemo } from "react";
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
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

function getWorkflowStatusMeta(workflowState) {
  if (workflowState === "checking_conditions") {
    return { label: "Checking conditions...", variant: "info" };
  }

  if (workflowState === "validating") {
    return { label: "Validating eligibility...", variant: "info" };
  }

  if (workflowState === "fraud_check") {
    return { label: "Processing claim...", variant: "warning" };
  }

  if (workflowState === "approved") {
    return { label: "Claim Approved ✅", variant: "success" };
  }

  if (workflowState === "flagged") {
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
    coverageLoading,
    requestLocation,
    refreshRisk,
    startCoverageCheck
  } = useAppContext();
  const { width } = useWindowDimensions();
  const isCompactScreen = width < 390;

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
  const workflowMeta = useMemo(() => getWorkflowStatusMeta(workflowState), [workflowState]);
  const liveRiskLabel = riskLoading ? "CHECKING" : compactRiskLabel;
  const policyReady = !policyLoading && !!policy;
  const premiumValue = policyReady ? `${formatRupee(policy.premium)}/week` : "Loading...";
  const meanIncomeValue = policyReady ? `${formatRupee(policy.meanIncome)}/day` : "Loading...";
  const coverageValue = policyReady ? `${formatRupee(policy.coverageAmount)}/day` : "Loading...";

  const handleCheckCoverage = React.useCallback(async () => {
    const result = await startCoverageCheck();
    if (result?.approved) {
      navigation.navigate("Payout");
    }
  }, [navigation, startCoverageCheck]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
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
            <StatusBadge label={liveRiskLabel} variant={riskVariant} />
          </View>
          <View style={[styles.summaryStatsRow, isCompactScreen ? styles.summaryStatsRowCompact : null]}>
            <SummaryStat label="Average Daily Income" value={meanIncomeValue} />
            <SummaryStat label="Daily Coverage" value={coverageValue} />
          </View>
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

        <Card style={styles.messageCard}>
          <Text style={styles.messageHeading}>Automation Feed</Text>
          <Text style={styles.feedItem}>Checking live conditions...</Text>
          <Text style={styles.feedItem}>Heavy rain detected</Text>
          <Text style={styles.feedItem}>Air quality unsafe</Text>
          <Text style={styles.feedItem}>System evaluating eligibility...</Text>
        </Card>

        <Button
          disabled={coverageLoading}
          loading={coverageLoading}
          onPress={handleCheckCoverage}
          style={styles.primaryAction}
          title="Check Coverage"
        />

        <View style={styles.inlineStatusRow}>
          <Text style={styles.inlineStatusLabel}>Workflow</Text>
          <StatusBadge label={workflowMessage || workflowMeta.label} variant={workflowMeta.variant} />
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
    paddingBottom: 100,
    paddingHorizontal: 20,
    paddingTop: 20
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
  primaryAction: {
    marginBottom: appTheme.spacing.sm,
    marginTop: appTheme.spacing.sm,
    width: "100%"
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
