import React, { memo, useMemo } from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import Header from "../components/Header";
import ProgressBar from "../components/ProgressBar";
import StatusBadge from "../components/StatusBadge";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function RiskScreen() {
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
  }
});

export default memo(RiskScreen);
