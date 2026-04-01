import React from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

const colorMap = {
  danger: appTheme.colors.danger,
  info: appTheme.colors.primary,
  success: appTheme.colors.accent,
  warning: appTheme.colors.warning
};

export default function StepLoader({ label, tone = "warning" }) {
  const color = colorMap[tone] || appTheme.colors.primary;

  return (
    <View style={styles.container}>
      <ActivityIndicator color={color} size="small" />
      <Text style={[styles.label, { color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    flexDirection: "row",
    marginTop: appTheme.spacing.sm
  },
  label: {
    fontSize: 14,
    fontWeight: "700",
    marginLeft: appTheme.spacing.xs
  }
});
