import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

const statusMap = {
  success: {
    background: "#DDF8EE",
    color: "#008E67"
  },
  warning: {
    background: "#FFF4D7",
    color: "#A36D00"
  },
  danger: {
    background: "#FFE3E3",
    color: "#B92C2C"
  },
  info: {
    background: "#EAF1F8",
    color: appTheme.colors.primary
  }
};

export default function StatusBadge({ label, variant = "info", style }) {
  const palette = statusMap[variant] || statusMap.info;

  return (
    <View style={[styles.badge, { backgroundColor: palette.background }, style]}>
      <Text style={[styles.label, { color: palette.color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderRadius: appTheme.radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 6
  },
  label: {
    fontSize: 12,
    fontWeight: "700"
  }
});
