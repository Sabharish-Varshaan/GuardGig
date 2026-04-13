import React, { memo, useMemo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { SafeAreaView } from "react-native-safe-area-context";

import Header from "../components/Header";
import NeonCard from "../components/NeonCard";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

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

function PayoutScreen() {
  const tabBarHeight = useBottomTabBarHeight();
  const { workflowState, payoutAmount, claimsHistory, policy, eligibilityMessage, payoutDetails } = useAppContext();
  const contentStyle = useMemo(
    () => ({
      justifyContent: "center",
      minHeight: "100%",
      paddingBottom: tabBarHeight + 14,
      paddingHorizontal: appTheme.spacing.sm,
      paddingTop: appTheme.spacing.md
    }),
    [tabBarHeight]
  );

  const latestClaim = claimsHistory[0] || null;
  const isCoverageEligible = !!policy && policy.status === "active" && policy.eligibilityStatus === "eligible" && policy.paymentStatus === "success";
  const latestAmount = isCoverageEligible ? (payoutAmount || latestClaim?.amount || 0) : 0;
  const payoutReason = !isCoverageEligible
    ? "Coverage is inactive during waiting period"
    : latestClaim
      ? latestClaim.reason || (latestClaim.type === "aqi" ? "Credited due to unsafe air quality" : "Credited due to heavy rainfall")
      : "Awaiting verified trigger";
  const transactionId = latestClaim?.transactionId || "--";
  const paidAt = latestClaim?.paidAt || "--";
  const paymentStatus = latestClaim?.paymentStatus || "pending";

  const payoutMeta = useMemo(() => {
    if (!isCoverageEligible) {
      return {
        badge: "Coverage Locked",
        description: eligibilityMessage,
        tone: "warning"
      };
    }

    if (workflowState === "approved") {
      return {
        badge: "Payout Successful",
        description: "Funds credited from automated trigger approval.",
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
      description: "Payout appears after a trigger-based approval.",
      tone: "info"
    };
  }, [eligibilityMessage, isCoverageEligible, workflowState]);
  const payoutTime = latestClaim ? formatRelativeTime(latestClaim.createdAt) : "--";

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={contentStyle} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Transparent payout visibility from trigger to settlement"
          title="Payout"
          rightElement={<StatusBadge label={payoutMeta.badge} variant={payoutMeta.tone} />}
        />

        <NeonCard glow style={styles.payoutCard} variant="gradient">
          <Text style={styles.highlightLabel}>Current Payout</Text>
          <Text style={styles.highlightValue}>{formatRupee(latestAmount)}</Text>
          <Text style={styles.highlightSub}>{payoutReason}</Text>
          <Text style={styles.highlightSubMuted}>{payoutTime}</Text>
          {!payoutDetails?.hasPayoutMethod && (
            <Text style={styles.warningText}>Please add payout details to receive compensation</Text>
          )}
          <Text style={styles.stateMeta}>{payoutMeta.description}</Text>
        </NeonCard>

        <NeonCard style={styles.detailCard} variant="elevated">
          <Text style={styles.detailTitle}>Settlement Details</Text>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Payment Status</Text>
            <Text style={styles.detailValue}>{paymentStatus}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Transaction ID</Text>
            <Text style={styles.detailValue}>{transactionId}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Paid At</Text>
            <Text style={styles.detailValue}>{paidAt}</Text>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Reason</Text>
            <Text style={styles.detailValue}>{payoutReason}</Text>
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
    justifyContent: "center",
    minHeight: "100%",
    paddingBottom: 80,
    paddingHorizontal: appTheme.spacing.sm,
    paddingTop: appTheme.spacing.md
  },
  payoutCard: {
    alignItems: "center",
    paddingVertical: appTheme.spacing.xl
  },
  detailCard: {
    marginTop: appTheme.spacing.md,
    paddingVertical: appTheme.spacing.lg
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
    fontSize: 48,
    marginTop: appTheme.spacing.xs
  },
  highlightSub: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 15,
    textAlign: "center",
    lineHeight: 22,
    marginTop: appTheme.spacing.sm
  },
  highlightSubMuted: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    textAlign: "center",
    marginTop: appTheme.spacing.xs
  },
  warningText: {
    color: appTheme.colors.warning,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginTop: appTheme.spacing.sm,
    textAlign: "center"
  },
  stateMeta: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: appTheme.spacing.md,
    textAlign: "center"
  },
  detailTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 16,
    marginBottom: appTheme.spacing.sm
  },
  detailRow: {
    borderTopColor: appTheme.colors.borderSoft,
    borderTopWidth: 1,
    paddingVertical: appTheme.spacing.sm
  },
  detailLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13,
    textTransform: "uppercase"
  },
  detailValue: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 15,
    marginTop: 4
  }
});

export default memo(PayoutScreen);