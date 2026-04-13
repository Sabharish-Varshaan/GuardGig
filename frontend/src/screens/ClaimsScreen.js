import React, { memo, useMemo } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";

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

  return item.triggerType === "aqi" ? "AQI" : "Rain";
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

function ClaimsScreen() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = useBottomTabBarHeight();
  const { claimsHistory, claimsLoading, dataError, refreshClaims, policy, demoMode } = useAppContext();

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
          <Text style={styles.summaryText}>Payouts are created by backend trigger checks. There is no manual payout action in this app.</Text>
          <Text style={styles.summaryText}>{isPolicyActive ? "Your policy is active and monitoring is enabled." : "Activate your policy to begin automated coverage."}</Text>
        </Card>

        <Card style={styles.summaryCard}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Payout History</Text>
            <StatusBadge label={claimsHistory.length > 0 ? `${claimsHistory.length} records` : "Empty"} variant={claimsHistory.length > 0 ? "success" : "info"} />
          </View>

          {claimsLoading && (
            <View style={styles.loadingRow}>
              <ActivityIndicator color={appTheme.colors.accentPrimary} />
              <Text style={styles.loadingText}>Refreshing payouts...</Text>
            </View>
          )}

          {!!dataError && <Text style={styles.errorText}>{dataError}</Text>}

          {claimsHistory.length === 0 ? (
            <Text style={styles.emptyText}>No payouts yet. You are protected when disruptions occur.</Text>
          ) : (
            claimsHistory.map((item) => (
              <View key={String(item.id)} style={styles.payoutItem}>
                <View style={styles.payoutTopRow}>
                  <Text style={styles.payoutTitle}>{`${getTriggerLabel(item)} (${getSeverityLabel(item.severity)})`}</Text>
                  <StatusBadge
                    label={item.status === "approved" || item.paymentStatus === "paid" ? "Credited" : item.status}
                    variant={item.status === "approved" || item.paymentStatus === "paid" ? "success" : "warning"}
                  />
                </View>
                <Text style={styles.payoutAmount}>{`${item.payoutPercentage ? `${item.payoutPercentage}%` : "--"} • ${formatRupee(item.amount)} credited`}</Text>
                <View style={styles.metaGrid}>
                  <Text style={styles.metaText}>Date: {formatDateTime(item.paidAt || item.createdAt)}</Text>
                  <Text style={styles.metaText}>Trigger: {getTriggerLabel(item)}</Text>
                  <Text style={styles.metaText}>Severity: {getSeverityLabel(item.severity)}</Text>
                  <Text style={styles.metaText}>Payout %: {item.payoutPercentage ? `${item.payoutPercentage}%` : "--"}</Text>
                  <Text style={styles.metaText}>Amount: {formatRupee(item.amount)}</Text>
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
    fontSize: 14,
    marginTop: appTheme.spacing.xs
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