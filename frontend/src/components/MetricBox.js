import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

const toneMap = {
  safe: {
    accent: appTheme.colors.semanticSafe,
    border: appTheme.colors.successBorder,
    bg: appTheme.colors.successSoft
  },
  warning: {
    accent: appTheme.colors.semanticWarning,
    border: appTheme.colors.warningBorder,
    bg: appTheme.colors.warningSoft
  },
  danger: {
    accent: appTheme.colors.semanticHighRisk,
    border: appTheme.colors.dangerBorder,
    bg: appTheme.colors.dangerSoft
  },
  info: {
    accent: appTheme.colors.semanticPayout,
    border: appTheme.colors.infoBorder,
    bg: appTheme.colors.infoSoft
  }
};

export default function MetricBox({ label, value, helper, tone = "info", style }) {
  const meta = toneMap[tone] || toneMap.info;

  return (
    <View style={[styles.box, { backgroundColor: meta.bg, borderColor: meta.border }, style]}>
      <Text style={styles.label}>{label}</Text>
      <Text style={[styles.value, { color: meta.accent }]}>{value}</Text>
      {!!helper && <Text style={styles.helper}>{helper}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  box: {
    borderRadius: appTheme.radius.soft,
    borderWidth: 1,
    flex: 1,
    minHeight: 136,
    paddingHorizontal: appTheme.spacing.sm,
    paddingVertical: appTheme.spacing.sm
  },
  label: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 13,
    letterSpacing: 0.5,
    textTransform: "uppercase"
  },
  value: {
    fontFamily: "Orbitron_700Bold",
    fontSize: 32,
    marginTop: appTheme.spacing.sm
  },
  helper: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_500Medium",
    fontSize: 14,
    lineHeight: 20,
    marginTop: appTheme.spacing.sm
  }
});