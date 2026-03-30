import React from "react";
import { ScrollView, StyleSheet, Switch, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Card from "../components/Card";
import Header from "../components/Header";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

function ToggleRow({ label, value, onValueChange, description }) {
  return (
    <View style={styles.toggleRow}>
      <View style={styles.toggleLeft}>
        <Text style={styles.toggleLabel}>{label}</Text>
        <Text style={styles.toggleDescription}>{description}</Text>
      </View>
      <Switch
        onValueChange={onValueChange}
        thumbColor={value ? appTheme.colors.accent : appTheme.colors.switchThumbOff}
        trackColor={{ false: appTheme.colors.switchTrackOff, true: appTheme.colors.switchTrackOn }}
        value={value}
      />
    </View>
  );
}

export default function SettingsScreen() {
  const {
    notificationsEnabled,
    setNotificationsEnabled,
    themeEnabled,
    setThemeEnabled
  } = useAppContext();

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Header
          subtitle="Control alerts and app preferences for your insurance experience"
          title="Settings"
        />

        <Card style={styles.cardGap}>
          <ToggleRow
            description="Receive payout and risk alerts"
            label="Notifications"
            onValueChange={setNotificationsEnabled}
            value={notificationsEnabled}
          />
          <ToggleRow
            description="Preview dark mode preference"
            label="Theme Toggle"
            onValueChange={setThemeEnabled}
            value={themeEnabled}
          />
        </Card>

        <Card>
          <Text style={styles.aboutTitle}>About</Text>
          <Text style={styles.aboutBody}>
            GigShield AI is an AI-powered parametric insurance assistant built for delivery workers. It estimates risk and triggers payouts automatically based on disruption conditions.
          </Text>
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
  toggleRow: {
    alignItems: "center",
    borderBottomColor: appTheme.colors.border,
    borderBottomWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: appTheme.spacing.md
  },
  toggleLeft: {
    flex: 1,
    paddingRight: appTheme.spacing.sm
  },
  toggleLabel: {
    color: appTheme.colors.primary,
    fontSize: 16,
    fontWeight: "700"
  },
  toggleDescription: {
    color: appTheme.colors.textSecondary,
    fontSize: 13,
    fontWeight: "600",
    marginTop: appTheme.spacing.xs
  },
  aboutTitle: {
    color: appTheme.colors.primary,
    fontSize: 18,
    fontWeight: "700",
    marginBottom: appTheme.spacing.sm
  },
  aboutBody: {
    color: appTheme.colors.textSecondary,
    fontSize: 14,
    fontWeight: "600",
    lineHeight: 20
  }
});
