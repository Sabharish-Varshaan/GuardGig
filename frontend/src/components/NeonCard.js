import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { appTheme } from "../styles/theme";

export default function NeonCard({ children, style, variant = "default", glow = false }) {
  const isGradient = variant === "gradient";

  if (isGradient) {
    return (
      <LinearGradient
        colors={[appTheme.colors.gradientDarkStart, appTheme.colors.gradientDarkEnd]}
        end={{ x: 1, y: 1 }}
        start={{ x: 0, y: 0 }}
        style={[styles.card, styles.gradientCard, glow ? appTheme.shadows.glow : null, style]}
      >
        {children}
      </LinearGradient>
    );
  }

  return (
    <View
      style={[
        styles.card,
        variant === "elevated" ? styles.elevated : null,
        glow ? appTheme.shadows.glow : null,
        style
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: appTheme.colors.bgCard,
    borderColor: appTheme.colors.borderSubtle,
    borderRadius: appTheme.radius.card,
    borderWidth: 1,
    paddingHorizontal: appTheme.spacing.sm,
    paddingVertical: 20,
    ...appTheme.shadows.card
  },
  elevated: {
    backgroundColor: appTheme.colors.bgElevated,
    borderColor: appTheme.colors.borderStrong
  },
  gradientCard: {
    borderColor: appTheme.colors.borderStrong
  }
});