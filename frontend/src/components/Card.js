import React from "react";
import { StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { appTheme } from "../styles/theme";

export default function Card({ children, style, gradient = false }) {
  if (gradient) {
    return (
      <LinearGradient
        colors={[appTheme.colors.gradientA, appTheme.colors.gradientB]}
        end={{ x: 1, y: 1 }}
        start={{ x: 0, y: 0 }}
        style={[styles.card, styles.gradientCard, style]}
      >
        {children}
      </LinearGradient>
    );
  }

  return <View style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: appTheme.colors.cardTint,
    borderColor: appTheme.colors.border,
    borderRadius: appTheme.radius.card,
    borderWidth: 1,
    padding: appTheme.spacing.lg,
    ...appTheme.shadows.card
  },
  gradientCard: {
    borderColor: appTheme.colors.overlay
  }
});
