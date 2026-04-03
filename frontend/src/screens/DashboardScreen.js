import React, { useMemo } from "react";
import { ScrollView, StyleSheet, Text, View, useWindowDimensions } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import LogPanel from "../components/LogPanel";
import MetricBox from "../components/MetricBox";
import RiskBanner from "../components/RiskBanner";
import StatusBadge from "../components/StatusBadge";
import StatusCard from "../components/StatusCard";
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

function formatRupee(value) {
  return `₹${value}`;
}

function getVariantFromRiskLevel(level) {
  const normalized = (level || "Low").toLowerCase();

  if (normalized === "high") {
    return "danger";
  }

  if (normalized === "medium") {
    return "warning";
  }

  return "success";
}

function getVariantFromSeverity(severity) {
  const normalized = (severity || "normal").toLowerCase();

  if (normalized === "high") {
    return "danger";
  }

  if (normalized === "moderate") {
    return "warning";
  }

  return "success";
}

function getFraudStatus(workflowState) {
  if (workflowState === "checking_conditions" || workflowState === "validating") {
    return { label: "Fraud Check: Pending", variant: "info" };
  }

  if (workflowState === "fraud_check") {
    return { label: "Fraud Check: Verifying", variant: "warning" };
  }

  if (workflowState === "flagged") {
    return { label: "Fraud Check: Verification Required", variant: "danger" };
  }

  if (workflowState === "approved") {
    return { label: "Fraud Check: Passed", variant: "success" };
  }

  return { label: "Fraud Check: Awaiting Request", variant: "info" };
}

export default function DashboardScreen({ navigation }) {
  const {
    user,
    policy,
    risk,
    workflowState,
    payoutAmount,
    movementScore,
    eventLogs,
    startCoverageCheck
  } = useAppContext();
  const { width } = useWindowDimensions();
  const isCompactScreen = width < 390;

  const isWorkflowRunning =
    workflowState === "checking_conditions" ||
    workflowState === "validating" ||
    workflowState === "fraud_check";

  const riskVariant = useMemo(() => getVariantFromRiskLevel(risk.level), [risk.level]);
  const conditionVariant = useMemo(() => getVariantFromSeverity(risk.severity), [risk.severity]);
  const fraudMeta = useMemo(() => getFraudStatus(workflowState), [workflowState]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Your income is protected"
          title={`Hello, ${user.fullName || "Ramesh"} 👋`}
          rightElement={<StatusBadge label={risk.level || "Medium"} variant={riskVariant} />}
        />

        <Card gradient style={styles.heroCard}>
          <Text style={styles.heroCaption}>Policy Snapshot</Text>
          <View style={styles.heroRow}>
            <View>
              <Text style={styles.heroLabel}>Weekly Income</Text>
              <Text style={styles.heroValue}>{formatRupee(Number(user.weeklyIncome) || 7000)}</Text>
            </View>
            <View>
              <Text style={styles.heroLabel}>Premium</Text>
              <Text style={styles.heroValue}>{`${formatRupee(policy.premium)}/week`}</Text>
            </View>
          </View>
          <View style={styles.heroRiskRow}>
            <Text style={styles.heroRiskText}>Risk Level</Text>
            <StatusBadge label={risk.level || "Medium"} variant={riskVariant} />
          </View>
        </Card>

        <View style={[styles.metricGrid, isCompactScreen ? styles.metricGridCompact : null]}>
          <MetricBox
            helper="live rainfall"
            label="Rain"
            tone={risk.rain >= 60 ? "danger" : risk.rain >= 45 ? "warning" : "safe"}
            value={`${risk.rain} mm`}
            style={isCompactScreen ? styles.metricBoxCompact : null}
          />
          <MetricBox
            helper="air quality"
            label="AQI"
            tone={risk.aqi >= 300 ? "danger" : risk.aqi >= 200 ? "warning" : "safe"}
            value={`${risk.aqi}`}
            style={isCompactScreen ? styles.metricBoxCompact : null}
          />
        </View>

        <Card style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Live Conditions</Text>
            <StatusBadge label={risk.status || "Normal"} variant={conditionVariant} />
          </View>
          <InfoRow icon="🌧️" label="Rain" value={`${risk.rain} mm`} />
          <InfoRow icon="🌫️" label="AQI" value={`${risk.aqi}`} />
          <InfoRow icon="🌡️" label="Temp" value={`${risk.temp}°C`} />
        </Card>

        <RiskBanner severity={risk.severity} text={risk.status} />

        {risk.isHighRisk && (
          <Button
            disabled={isWorkflowRunning}
            loading={isWorkflowRunning}
            onPress={startCoverageCheck}
            style={styles.checkCoverageButton}
            title="Check Coverage"
          />
        )}

        <StatusCard
          movementScore={movementScore}
          payoutAmount={payoutAmount}
          workflowState={workflowState}
        />

        <Card style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>Coverage</Text>
          <InfoRow icon="🛡️" label="Plan" value={policy.planName} />
          <InfoRow icon="💰" label="Coverage Left" value={formatRupee(policy.coverageLeft)} />
          <InfoRow icon="🔁" label="Renewal" value={policy.renewalIn} />
          <View style={styles.fraudBadgeWrap}>
            <StatusBadge label={fraudMeta.label} variant={fraudMeta.variant} />
          </View>
        </Card>

        <LogPanel logs={eventLogs} />

        <View style={styles.actionGroup}>
          <Button onPress={() => navigation.navigate("Policy")} title="View Policy" />
          <Button
            onPress={() => navigation.navigate("Claims")}
            style={styles.secondaryAction}
            title="Open Claims"
            variant="secondary"
          />
          <Button
            onPress={() => navigation.navigate("Payout")}
            style={styles.secondaryAction}
            title="View Payout"
            variant="ghost"
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  content: {
    paddingBottom: appTheme.spacing.xxl + 200,
    paddingHorizontal: appTheme.spacing.sm,
    paddingTop: appTheme.spacing.sm
  },
  heroCard: {
    marginBottom: appTheme.spacing.lg,
    paddingBottom: appTheme.spacing.md
  },
  heroCaption: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 12,
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  metricGrid: {
    flexDirection: "row",
    gap: appTheme.spacing.sm,
    marginBottom: appTheme.spacing.md
  },
  metricGridCompact: {
    flexDirection: "column"
  },
  metricBoxCompact: {
    flex: 0,
    width: "100%"
  },
  heroRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: appTheme.spacing.sm
  },
  heroLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14
  },
  heroValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 26,
    marginTop: appTheme.spacing.xs
  },
  heroRiskRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: appTheme.spacing.md
  },
  heroRiskText: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 16
  },
  sectionCard: {
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
  infoRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.sm,
    paddingVertical: 2
  },
  infoLabel: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 16
  },
  infoValue: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 16
  },
  fraudBadgeWrap: {
    marginTop: appTheme.spacing.sm
  },
  checkCoverageButton: {
    marginBottom: appTheme.spacing.lg
  },
  actionGroup: {
    marginBottom: appTheme.spacing.xxl,
    marginTop: appTheme.spacing.md
  },
  secondaryAction: {
    marginTop: appTheme.spacing.md
  }
});
