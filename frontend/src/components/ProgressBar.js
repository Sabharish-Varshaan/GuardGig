import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";

import { appTheme } from "../styles/theme";

export default function ProgressBar({
  label,
  value,
  unit = "",
  progress = 0,
  color = appTheme.colors.accent,
  rightLabel
}) {
  const clamped = Math.max(0, Math.min(progress, 100));
  const progressAnim = useRef(new Animated.Value(clamped)).current;

  useEffect(() => {
    Animated.timing(progressAnim, {
      duration: appTheme.motion.duration.normal,
      toValue: clamped,
      useNativeDriver: false
    }).start();
  }, [clamped, progressAnim]);

  const widthInterpolated = progressAnim.interpolate({
    inputRange: [0, 100],
    outputRange: ["0%", "100%"]
  });

  return (
    <View style={styles.wrapper}>
      <View style={styles.headerRow}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.valueText}>{rightLabel || `${value}${unit}`}</Text>
      </View>
      <View style={styles.track}>
        <Animated.View style={[styles.fill, { backgroundColor: color, width: widthInterpolated }]} />
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
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 16
  },
  valueText: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 16
  },
  track: {
    backgroundColor: appTheme.colors.semanticSurfaceMuted,
    borderColor: appTheme.colors.borderSubtle,
    borderRadius: appTheme.radius.pill,
    borderWidth: 1,
    height: 10,
    overflow: "hidden"
  },
  fill: {
    borderRadius: appTheme.radius.pill,
    height: 10
  }
});
