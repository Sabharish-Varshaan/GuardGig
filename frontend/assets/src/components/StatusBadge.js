import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

const statusMap = {
  success: {
    background: appTheme.colors.successSoft,
    color: appTheme.colors.successText,
    border: appTheme.colors.successBorder
  },
  warning: {
    background: appTheme.colors.warningSoft,
    color: appTheme.colors.warningText,
    border: appTheme.colors.warningBorder
  },
  danger: {
    background: appTheme.colors.dangerSoft,
    color: appTheme.colors.dangerText,
    border: appTheme.colors.dangerBorder
  },
  info: {
    background: appTheme.colors.infoSoft,
    color: appTheme.colors.primary,
    border: appTheme.colors.infoBorder
  }
};

export default function StatusBadge({ label, variant = "info", style }) {
  const palette = statusMap[variant] || statusMap.info;

  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: palette.background,
          borderColor: palette.border
        },
        style
      ]}
    >
      <Text style={[styles.label, { color: palette.color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderWidth: 1,
    borderRadius: appTheme.radius.pill,
    paddingHorizontal: 11,
    paddingVertical: 6
  },
  label: {
    fontSize: 11,
    letterSpacing: 0.3,
    fontWeight: "700"
  }
});
