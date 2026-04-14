import React, { memo, useMemo } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

import Button from "../components/Button";
import Card from "../components/Card";
import Header from "../components/Header";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

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

function getTriggerLabel(item) {
  if (item.triggerLabel) {
    return item.triggerLabel;
  }

  const triggerType = String(item.triggerType || "").toLowerCase();
  if (triggerType === "aqi") {
    return "AQI";
  }
  if (triggerType === "heat") {
    return "HEAT";
  }
  return "Rain";
}

function getTriggerEmoji(item) {
  const triggerType = String(item.triggerType || "").toLowerCase();
  if (triggerType === "aqi") {
    return "🌫️";
  }
  if (triggerType === "heat") {
    return "🔥";
  }
  return "🌧️";
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

function getDestinationLabel(item) {
  const method = String(item.payoutMethod || "").toLowerCase();
  const destination = item.maskedAccount || "--";

  if (method === "upi") {
    return `UPI: ${destination}`;
  }

  if (method === "bank") {
    return `Bank: ${destination}`;
  }

  return "Destination pending";
}

function maskTransactionId(transactionId) {
  if (!transactionId) {
    return "--";
  }
  if (transactionId.length <= 5) {
    return transactionId;
  }
  return `${transactionId.slice(0, 5)}***`;
}

function ClaimsScreen() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = useBottomTabBarHeight();
  const { claimsHistory, claimsLoading, dataError, refreshClaims, policy, demoMode, payoutDetails } = useAppContext();

  useFocusEffect(
    React.useCallback(() => {
      refreshClaims().catch(() => {});
      return undefined;
    }, [refreshClaims])
  );

  const listContentStyle = useMemo(
    () => ({
      paddingBottom: tabBarHeight + insets.bottom + 20,
      paddingHorizontal: appTheme.spacing.sm,
      paddingTop: appTheme.spacing.sm
    }),
    [insets.bottom, tabBarHeight]
  );

  const isPolicyActive = !!policy && policy.status === "active" && policy.paymentStatus === "success";

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={listContentStyle} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Read-only record of backend-driven settlements"
          title="Payouts"
          rightElement={<StatusBadge label={demoMode ? "Demo Mode" : "Live"} variant={demoMode ? "warning" : "success"} />}
        />

        <Card style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Automation Summary</Text>
          {demoMode && (
            <View style={styles.demoBanner}>
              <Text style={styles.demoBannerText}>Demo Mode Active</Text>
            </View>
          )}
          <Text style={styles.summaryText}>Payouts are created by backend trigger checks. There is no manual payout action in this app.</Text>
          <Text style={styles.summaryText}>{isPolicyActive ? "Your policy is active and monitoring is enabled." : "Activate your policy to begin automated coverage."}</Text>
          {!payoutDetails?.hasPayoutMethod && (
            <Text style={styles.warningText}>Please add payout details to receive compensation</Text>
          )}
        </Card>

        <Card style={styles.summaryCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Payout History</Text>
            <Button onPress={() => refreshClaims().catch(() => {})} title="Retry" variant="secondary" />
          </View>

          {claimsLoading && (
            <View style={styles.loadingRow}>
              <ActivityIndicator color={appTheme.colors.accentPrimary} />
              <Text style={styles.loadingText}>Refreshing payouts...</Text>
            </View>
          )}

          {!!dataError && <Text style={styles.errorText}>{dataError}</Text>}

          {claimsHistory.length === 0 ? (
            <Text style={styles.emptyText}>You are protected. Payouts will be automatic.</Text>
          ) : (
            claimsHistory.map((item) => (
              <View key={String(item.id)} style={styles.payoutItem}>
                <View style={styles.payoutTopRow}>
                  <Text style={styles.payoutTitle}>{`${getTriggerEmoji(item)} ${getTriggerLabel(item)} (${getSeverityLabel(item.severity)})`}</Text>
                  <StatusBadge
                    label={item.status === "approved" || ["paid", "credited"].includes(item.paymentStatus) ? "Credited" : item.status}
                    variant={item.status === "approved" || ["paid", "credited"].includes(item.paymentStatus) ? "success" : "warning"}
                  />
                </View>
                <Text style={styles.payoutAmount}>{`💸 ${item.payoutPercentage ? `${item.payoutPercentage}%` : "--"} • ${formatRupee(item.amount)} credited`}</Text>
                <Text style={styles.destinationText}>{`${formatRupee(item.amount)} credited to ${getDestinationLabel(item)}`}</Text>
                <View style={styles.metaGrid}>
                  <Text style={styles.metaText}>Date: {formatDateTime(item.paidAt || item.createdAt)}</Text>
                  <Text style={styles.metaText}>Trigger: {getTriggerLabel(item)}</Text>
                  <Text style={styles.metaText}>Severity: {getSeverityLabel(item.severity)}</Text>
                  <Text style={styles.metaText}>Payout %: {item.payoutPercentage ? `${item.payoutPercentage}%` : "--"}</Text>
                  <Text style={styles.metaText}>Status: {item.paymentStatus || "pending"}</Text>
                  <Text style={styles.metaText}>Transaction: {maskTransactionId(item.transactionId)}</Text>
                </View>
                {!!item.reason && <Text style={styles.reasonText}>{item.reason}</Text>}
              </View>
            ))
          )}
        </Card>

        <Card style={styles.summaryCard}>
          <Text style={styles.sectionTitle}>Trust Layer</Text>
          <Text style={styles.summaryText}>Trigger checks, fraud checks, and settlement updates are all driven by the backend and reflected here after sync.</Text>
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

export default memo(ClaimsScreen);

const styles = StyleSheet.create({
  screen: {
    backgroundColor: appTheme.colors.background,
    flex: 1
  },
  summaryCard: {
    marginBottom: appTheme.spacing.md
  },
  summaryTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18,
    marginBottom: appTheme.spacing.xs
  },
  summaryText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 20,
    marginTop: appTheme.spacing.xs
  },
  demoBanner: {
    backgroundColor: appTheme.colors.warningSoft,
    borderColor: appTheme.colors.warningBorder,
    borderRadius: appTheme.radius.soft,
    borderWidth: 1,
    marginBottom: appTheme.spacing.xs,
    marginTop: appTheme.spacing.xs,
    paddingHorizontal: appTheme.spacing.xs,
    paddingVertical: appTheme.spacing.xs
  },
  demoBannerText: {
    color: appTheme.colors.warningText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14
  },
  warningText: {
    color: appTheme.colors.warning,
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
    fontSize: 18
  },
  loadingRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: 10,
    marginBottom: appTheme.spacing.sm
  },
  loadingText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14
  },
  errorText: {
    color: appTheme.colors.dangerText,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginBottom: appTheme.spacing.sm
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
    fontSize: 18,
    marginTop: appTheme.spacing.xs
  },
  destinationText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    marginTop: 4
  },
  metaGrid: {
    marginTop: appTheme.spacing.sm
  },
  metaText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 13,
    lineHeight: 18,
    marginTop: 2
  },
  reasonText: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 13,
    lineHeight: 18,
    marginTop: appTheme.spacing.sm
  }
});