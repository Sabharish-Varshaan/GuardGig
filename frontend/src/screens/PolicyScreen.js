import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
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

export default function PolicyScreen() {
  const { policy, policyLoading, dataError, refreshPolicy } = useAppContext();

  useFocusEffect(
    React.useCallback(() => {
      refreshPolicy().catch(() => {});
      return undefined;
    }, [refreshPolicy])
  );

  const policyReady = !policyLoading && !!policy;
  const policyStatus = policyReady ? (policy.status === "active" ? "Active" : "Inactive") : "Loading...";

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Your policy is synced from backend"
          title="Policy"
          rightElement={<StatusBadge label={policyStatus} variant={policyReady ? (policyStatus === "Active" ? "success" : "warning") : "info"} />}
        />

        <Card style={styles.cardGap}>
          <Text style={styles.cardTitle}>Policy Details</Text>
          <Row label="Weekly Income" value={policyReady ? formatRupee(policy.weeklyIncome) : "Loading..."} />
          <Row label="Premium" value={policyReady ? `${formatRupee(policy.premium)}/week` : "Loading..."} />
          <Row label="Coverage" value={policyReady ? `${formatRupee(policy.coverageAmount)}/day` : "Loading..."} />
          <Row label="Status" value={policyStatus} />
          <Row label="Eligibility" value={policyReady ? policy.eligibilityStatus : "Loading..."} />
          <Row label="Worker Tier" value={policyReady ? policy.workerTier : "Loading..."} />
        </Card>

        <Card gradient style={styles.coverageCard}>
          <Text style={styles.coverageLabel}>Policy Start</Text>
          <Text style={styles.coverageValue}>{policyReady ? policy.policyStartDate || "Unavailable" : "Loading..."}</Text>
          <Text style={styles.coverageSub}>{policyLoading ? "Refreshing policy..." : "Live backend policy"}</Text>
        </Card>

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
  errorText: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14
  }
});
