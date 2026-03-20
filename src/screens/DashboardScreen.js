import React, { useMemo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import LogPanel from "../components/LogPanel";
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
          <Button onPress={() => navigation.navigate("Claims")} style={styles.secondaryAction} title="Open Claims" variant="secondary" />
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
    paddingBottom: appTheme.spacing.xxl,
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg
  },
  heroCard: {
    marginBottom: appTheme.spacing.md,
    paddingBottom: appTheme.spacing.md
  },
  heroCaption: {
    color: "#D8E9F4",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1,
    textTransform: "uppercase"
  },
  heroRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: appTheme.spacing.md
  },
  heroLabel: {
    color: "#D8E9F4",
    fontSize: 13,
    fontWeight: "600"
  },
  heroValue: {
    color: appTheme.colors.surface,
    fontSize: 26,
    fontWeight: "700",
    marginTop: 2
  },
  heroRiskRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: appTheme.spacing.md
  },
  heroRiskText: {
    color: appTheme.colors.surface,
    fontSize: 15,
    fontWeight: "700"
  },
  sectionCard: {
    marginBottom: appTheme.spacing.md
  },
  sectionHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.sm
  },
  sectionTitle: {
    color: appTheme.colors.primary,
    fontSize: 18,
    fontWeight: "700",
    marginBottom: appTheme.spacing.sm
  },
  infoRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.sm
  },
  infoLabel: {
    color: appTheme.colors.textPrimary,
    fontSize: 15,
    fontWeight: "600"
  },
  infoValue: {
    color: appTheme.colors.primary,
    fontSize: 15,
    fontWeight: "700"
  },
  fraudBadgeWrap: {
    marginTop: appTheme.spacing.xs
  },
  checkCoverageButton: {
    marginBottom: appTheme.spacing.md
  },
  actionGroup: {
    marginTop: appTheme.spacing.sm
  },
  secondaryAction: {
    marginTop: appTheme.spacing.sm
  }
});
