import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

const metaMap = {
  high: {
    accent: appTheme.colors.danger,
    background: appTheme.colors.dangerSoft,
    icon: "🔴"
  },
  moderate: {
    accent: appTheme.colors.warning,
    background: appTheme.colors.warningSoft,
    icon: "🟡"
  },
  normal: {
    accent: appTheme.colors.accentAlt,
    background: appTheme.colors.successSoft,
    icon: "🟢"
  }
};

export default function RiskBanner({ severity = "normal", text }) {
  const meta = metaMap[severity] || metaMap.normal;

  return (
    <View style={[styles.container, { backgroundColor: meta.background, borderColor: meta.accent }]}>
      <Text style={styles.icon}>{meta.icon}</Text>
      <Text style={[styles.text, { color: meta.accent }]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    borderRadius: appTheme.radius.soft,
    borderWidth: 1,
    flexDirection: "row",
    marginBottom: appTheme.spacing.md,
    paddingHorizontal: appTheme.spacing.md,
    paddingVertical: appTheme.spacing.sm
  },
  icon: {
    fontSize: 16,
    marginRight: appTheme.spacing.xs
  },
  text: {
    fontFamily: "Rajdhani_700Bold",
    fontSize: 14,
    letterSpacing: 0.2,
    textTransform: "uppercase"
  }
});
