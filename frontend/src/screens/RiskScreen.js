import React, { memo, useMemo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import Header from "../components/Header";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function RiskScreen() {
  const { risk } = useAppContext();

  const bannerMeta = useMemo(() => {
    const severity = (risk.severity || "none").toLowerCase();

    if (severity === "full") {
      return { label: "High Risk", variant: "danger" };
    }

    if (severity === "partial") {
      return { label: "Moderate", variant: "warning" };
    }

    return { label: "Safe", variant: "success" };
  }, [risk.severity]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Live conditions that influence your coverage"
          title="Risk"
          rightElement={<StatusBadge label="AI Live" variant="success" />}
        />

        <Card style={styles.bannerCard}>
          <View style={styles.bannerRow}>
            <Text style={styles.bannerTitle}>Risk Status</Text>
            <StatusBadge label={bannerMeta.label} variant={bannerMeta.variant} />
          </View>
          <Text style={styles.bannerBody}>{risk.status || "Normal conditions"}</Text>
        </Card>

        <Card style={styles.graphCard}>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Rainfall</Text>
            <Text style={styles.rowValue}>{risk.rain === null ? "--" : `${risk.rain} mm`}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>AQI</Text>
            <Text style={styles.rowValue}>{risk.aqi === null ? "--" : `${risk.aqi}`}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.rowLabel}>Severity</Text>
            <Text style={styles.rowValue}>{risk.severity || "none"}</Text>
          </View>
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
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 80
  },
  bannerCard: {
    marginBottom: appTheme.spacing.md
  },
  bannerRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.xs
  },
  bannerTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18
  },
  bannerBody: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    lineHeight: 18
  },
  graphCard: {
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

export default memo(RiskScreen);
