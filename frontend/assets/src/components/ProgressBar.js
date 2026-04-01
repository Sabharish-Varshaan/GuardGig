import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

export default function ProgressBar({
  label,
  value,
  unit = "",
  progress = 0,
  color = appTheme.colors.accent,
  rightLabel
}) {
  return (
    <View style={styles.wrapper}>
      <View style={styles.headerRow}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.valueText}>{rightLabel || `${value}${unit}`}</Text>
      </View>
      <View style={styles.track}>
        <View style={[styles.fill, { backgroundColor: color, width: `${Math.max(0, Math.min(progress, 100))}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: appTheme.spacing.md
  },
  headerRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: appTheme.spacing.xs
  },
  label: {
    color: appTheme.colors.textPrimary,
    fontSize: 15,
    fontWeight: "600"
  },
  valueText: {
    color: appTheme.colors.primary,
    fontSize: 15,
    fontWeight: "700"
  },
  track: {
    backgroundColor: appTheme.colors.mutedBlue,
    borderRadius: appTheme.radius.pill,
    height: 10,
    overflow: "hidden"
  },
  fill: {
    borderRadius: appTheme.radius.pill,
    height: 10
  }
});
