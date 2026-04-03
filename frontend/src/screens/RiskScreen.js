import React, { useMemo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import Header from "../components/Header";
import ProgressBar from "../components/ProgressBar";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

export default function RiskScreen() {
  const { risk } = useAppContext();

  const bannerMeta = useMemo(() => {
    const severity = (risk.severity || "normal").toLowerCase();

    if (severity === "high") {
      return { label: "High Risk", variant: "danger" };
    }

    if (severity === "moderate") {
      return { label: "Moderate", variant: "warning" };
    }

    return { label: "Normal", variant: "success" };
  }, [risk.severity]);

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Live weather and pollution inputs driving dynamic premium and payout decisions"
          title="Risk"
          rightElement={<StatusBadge label="AI Live" variant="success" />}
        />

        <Card style={styles.bannerCard}>
          <View style={styles.bannerRow}>
            <Text style={styles.bannerTitle}>Risk Status</Text>
            <StatusBadge label={bannerMeta.label} variant={bannerMeta.variant} />
          </View>
          <Text style={styles.bannerBody}>
            Current trigger signals indicate {risk.status || "Normal Conditions"}.
          </Text>
        </Card>

        <Card style={styles.graphCard}>
          <ProgressBar
            color={appTheme.colors.warning}
            label="Rainfall"
            progress={Math.min((Number(risk.rain) / 100) * 100, 100)}
            unit=" mm"
            value={risk.rain}
          />
          <ProgressBar
            color={appTheme.colors.danger}
            label="AQI"
            progress={Math.min((Number(risk.aqi) / 400) * 100, 100)}
            value={risk.aqi}
          />
          <ProgressBar
            color={appTheme.colors.accent}
            label="Temperature"
            progress={Math.min((Number(risk.temp) / 50) * 100, 100)}
            unit="°C"
            value={risk.temp}
          />
        </Card>

        <Card>
          <Text style={styles.legendTitle}>Status Legend</Text>
          <View style={styles.legendRow}>
            <View style={[styles.dot, { backgroundColor: appTheme.colors.accent }]} />
            <Text style={styles.legendText}>Normal</Text>
          </View>
          <View style={styles.legendRow}>
            <View style={[styles.dot, { backgroundColor: appTheme.colors.warning }]} />
            <Text style={styles.legendText}>Moderate</Text>
          </View>
          <View style={styles.legendRow}>
            <View style={[styles.dot, { backgroundColor: appTheme.colors.danger }]} />
            <Text style={styles.legendText}>High Risk</Text>
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
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.lg,
    paddingBottom: appTheme.spacing.xxl
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
    fontSize: 20
  },
  bannerBody: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15,
    lineHeight: 20
  },
  graphCard: {
    marginBottom: appTheme.spacing.md
  },
  legendTitle: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 17,
    marginBottom: appTheme.spacing.sm
  },
  legendRow: {
    alignItems: "center",
    flexDirection: "row",
    marginBottom: appTheme.spacing.xs
  },
  dot: {
    borderRadius: appTheme.radius.pill,
    height: 10,
    marginRight: appTheme.spacing.xs,
    width: 10
  },
  legendText: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 15
  }
});
