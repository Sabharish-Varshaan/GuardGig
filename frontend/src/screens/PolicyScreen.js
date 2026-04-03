import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
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
  const { policy } = useAppContext();

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Your weekly premium and payout thresholds are generated from risk behavior"
          title="Policy"
          rightElement={<StatusBadge label={policy.planName} variant="success" />}
        />

        <Card style={styles.cardGap}>
          <Text style={styles.cardTitle}>Premium Breakdown</Text>
          <Row label="Base" value={formatRupee(policy.base)} />
          <Row label="Risk" value={formatRupee(policy.riskAdjustment)} />
          <Row label="Event Factor" value={formatRupee(policy.eventFactor)} />
          <View style={styles.separator} />
          <Row label="Total Premium" value={`${formatRupee(policy.premium)}/week`} />
        </Card>

        <Card gradient style={styles.coverageCard}>
          <Text style={styles.coverageLabel}>Weekly Coverage</Text>
          <Text style={styles.coverageValue}>{formatRupee(policy.weeklyCoverage)}</Text>
          <Text style={styles.coverageSub}>{`Daily Payout: ${formatRupee(policy.dailyPayout)}`}</Text>
        </Card>

        <Card>
          <Text style={styles.cardTitle}>Renewal Information</Text>
          <Row label="Next Renewal" value={policy.renewalIn} />
          <Row label="Coverage Left" value={formatRupee(policy.coverageLeft)} />
        </Card>
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
  separator: {
    backgroundColor: appTheme.colors.border,
    height: 1,
    marginVertical: appTheme.spacing.xs
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
    fontSize: 40,
    marginTop: appTheme.spacing.xs
  },
  coverageSub: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15
  }
});
