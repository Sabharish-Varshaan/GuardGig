import React, { useMemo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Header from "../components/Header";
import NeonCard from "../components/NeonCard";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function formatRupee(value) {
  return `₹${value}`;
}

export default function PayoutScreen() {
  const { workflowState, payoutAmount, movementScore, claimsHistory } = useAppContext();

  const latestClaim = claimsHistory[0] || null;

  const payoutMeta = useMemo(() => {
    if (workflowState === "approved") {
      return {
        badge: "Payout Successful",
        description: "Funds are credited instantly after fraud-safe validation.",
        tone: "success"
      };
    }

    if (workflowState === "flagged") {
      return {
        badge: "Verification Required",
        description: "Payout is paused until movement checks are cleared.",
        tone: "warning"
      };
    }

    return {
      badge: "Awaiting Trigger",
      description: "Payout opens when disruption conditions cross policy thresholds.",
      tone: "info"
    };
  }, [workflowState]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Transparent payout visibility from trigger to settlement"
          title="Payout"
          rightElement={<StatusBadge label={payoutMeta.badge} variant={payoutMeta.tone} />}
        />

        <NeonCard glow variant="gradient">
          <Text style={styles.highlightLabel}>Current Eligible Amount</Text>
          <Text style={styles.highlightValue}>{formatRupee(payoutAmount || latestClaim?.amount || 0)}</Text>
          <Text style={styles.highlightSub}>{payoutMeta.description}</Text>
        </NeonCard>

        <NeonCard style={styles.sectionGap} variant="elevated">
          <Text style={styles.sectionTitle}>Settlement Readiness</Text>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Workflow State</Text>
            <Text style={styles.rowValue}>{workflowState.replaceAll("_", " ")}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Movement Score</Text>
            <Text style={styles.rowValue}>{movementScore}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Latest Claim</Text>
            <Text style={styles.rowValue}>{latestClaim?.status || "No claim yet"}</Text>
          </View>
        </NeonCard>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.bgPrimary,
    flex: 1
  },
  content: {
    paddingBottom: appTheme.spacing.xxl + 200,
    paddingHorizontal: appTheme.spacing.sm,
    paddingTop: appTheme.spacing.md
  },
  highlightLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    letterSpacing: 0.6,
    textTransform: "uppercase"
  },
  highlightValue: {
    color: appTheme.colors.accentSuccess,
    fontFamily: "Orbitron_700Bold",
    fontSize: 38,
    marginTop: appTheme.spacing.xs
  },
  highlightSub: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 15,
    lineHeight: 22,
    marginTop: appTheme.spacing.sm
  },
  sectionGap: {
    marginTop: appTheme.spacing.md
  },
  sectionTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18,
    marginBottom: appTheme.spacing.md
  },
  row: {
    alignItems: "center",
    borderTopColor: appTheme.colors.borderSubtle,
    borderTopWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: appTheme.spacing.sm
  },
  rowLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 16
  },
  rowValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 16,
    textTransform: "capitalize"
  }
});