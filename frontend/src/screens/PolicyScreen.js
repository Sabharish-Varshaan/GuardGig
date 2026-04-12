import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { useBottomTabBarHeight } from "@react-navigation/bottom-tabs";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import Button from "../components/Button";
import Header from "../components/Header";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function formatRupee(value) {
  return `₹${value}`;
}

function Row({ label, value }) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

export default function PolicyScreen({ navigation }) {
  const tabBarHeight = useBottomTabBarHeight();
  const { policy, policyLoading, dataError, refreshPolicy, eligibilityMessage, activatePolicyPayment, paymentLoading, paymentError } = useAppContext();
  const contentStyle = React.useMemo(
    () => ({
      paddingHorizontal: appTheme.spacing.lg,
      paddingTop: appTheme.spacing.lg,
      paddingBottom: tabBarHeight + 18
    }),
    [tabBarHeight]
  );

  useFocusEffect(
    React.useCallback(() => {
      refreshPolicy().catch(() => {});
      return undefined;
    }, [refreshPolicy])
  );

  const policyReady = !policyLoading && !!policy;
  const policyStatus = policyReady ? (policy.status === "active" ? "Active" : "Inactive") : "Loading...";
  const paymentStatus = policyReady ? (policy.paymentStatus === "success" ? "Paid" : "Pending") : "Loading...";

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={contentStyle} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Your policy is synced from backend"
          title="Policy"
          rightElement={<StatusBadge label={policyStatus} variant={policyReady ? (policyStatus === "Active" ? "success" : "warning") : "info"} />}
        />

        <Card style={styles.cardGap}>
          <Text style={styles.cardTitle}>Policy Details</Text>
          <Row label="Average Daily Income" value={policyReady ? formatRupee(policy.meanIncome) : "Loading..."} />
          <Row label="Weekly Income" value={policyReady ? formatRupee(policy.weeklyIncome) : "Loading..."} />
          <Row label="Premium" value={policyReady ? `${formatRupee(policy.premium)}/week` : "Loading..."} />
          <Row label="Coverage" value={policyReady ? `${formatRupee(policy.coverageAmount)}/day` : "Loading..."} />
          <Row label="Status" value={policyStatus} />
          <Row label="Payment Status" value={paymentStatus} />
          <Row label="Eligibility" value={policyReady ? policy.eligibilityStatus : "Loading..."} />
          <Row label="Worker Tier" value={policyReady ? policy.workerTier : "Loading..."} />
        </Card>

        {policyReady && policy.paymentStatus !== "success" && (
          <Card style={styles.warningCard}>
            <Text style={styles.warningText}>Premium payment is required before claims can be submitted.</Text>
            {!!paymentError && <Text style={styles.errorText}>{paymentError}</Text>}
            <Button
              loading={paymentLoading}
              onPress={async () => {
                const result = await activatePolicyPayment();
                if (result?.success && result?.orderId) {
                  navigation.navigate("Payment", {
                    orderId: result.orderId,
                    amount: result.amount,
                    paymentId: result.paymentId,
                    source: "policy"
                  });
                }
              }}
              style={styles.payButton}
              title={`Pay Now • ${formatRupee(policy.premium)}`}
            />
          </Card>
        )}

        <Card gradient style={styles.coverageCard}>
          <Text style={styles.coverageLabel}>Policy Start</Text>
          <Text style={styles.coverageValue}>{policyReady ? policy.policyStartDate || "Unavailable" : "Loading..."}</Text>
          <Text style={styles.coverageHint}>Coverage based on average income</Text>
          <Text style={styles.coverageSub}>{policyLoading ? "Refreshing policy..." : "Live backend policy"}</Text>
        </Card>

        {policyReady && policy.eligibilityStatus !== "eligible" && (
          <Card style={styles.warningCard}>
            <Text style={styles.warningText}>{eligibilityMessage}</Text>
          </Card>
        )}

        {!!dataError && <Text style={styles.errorText}>{dataError}</Text>}
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
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg,
    paddingBottom: appTheme.spacing.xxl
  },
  cardGap: {
    marginBottom: appTheme.spacing.md
  },
  cardTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18,
    marginBottom: appTheme.spacing.sm
  },
  row: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.sm
  },
  label: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15
  },
  value: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 17
  },
  coverageCard: {
    marginBottom: appTheme.spacing.md
  },
  coverageLabel: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 13,
    textTransform: "uppercase"
  },
  coverageValue: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 24,
    marginTop: appTheme.spacing.xs
  },
  coverageSub: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15
  },
  coverageHint: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: appTheme.spacing.xs
  },
  warningCard: {
    marginBottom: appTheme.spacing.md
  },
  payButton: {
    marginTop: appTheme.spacing.sm
  },
  warningText: {
    color: appTheme.colors.warningText,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14
  },
  errorText: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14
  }
});
