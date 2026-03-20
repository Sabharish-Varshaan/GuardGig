import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { appTheme } from "../styles/theme";

export default function Button({
  title,
  onPress,
  variant = "primary",
  style,
  disabled = false,
  loading = false
}) {
  const isSecondary = variant === "secondary";
  const isGhost = variant === "ghost";

  const label = (
    <Text
      style={[
        styles.label,
        isSecondary ? styles.secondaryLabel : null,
        isGhost ? styles.ghostLabel : null
      ]}
    >
      {title}
    </Text>
  );

  if (isSecondary || isGhost) {
    return (
      <Pressable
        disabled={disabled || loading}
        onPress={onPress}
        style={({ pressed }) => [
          styles.button,
          isSecondary ? styles.secondaryButton : styles.ghostButton,
          pressed && !disabled ? styles.pressed : null,
          disabled ? styles.disabled : null,
          style
        ]}
      >
        {loading ? <ActivityIndicator color={appTheme.colors.primary} /> : label}
      </Pressable>
    );
  }

  return (
    <Pressable
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [styles.button, pressed && !disabled ? styles.pressed : null, disabled ? styles.disabled : null, style]}
    >
      <LinearGradient
        colors={["#0B3C5D", "#165A86"]}
        end={{ x: 1, y: 1 }}
        start={{ x: 0, y: 0 }}
        style={styles.gradientButton}
      >
        {loading ? <ActivityIndicator color={appTheme.colors.surface} /> : label}
      </LinearGradient>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: appTheme.radius.soft,
    minHeight: 54,
    overflow: "hidden"
  },
  gradientButton: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 54,
    paddingHorizontal: appTheme.spacing.md
  },
  secondaryButton: {
    alignItems: "center",
    backgroundColor: appTheme.colors.surface,
    borderColor: appTheme.colors.primary,
    borderWidth: 1,
    justifyContent: "center",
    paddingHorizontal: appTheme.spacing.md
  },
  ghostButton: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: appTheme.spacing.sm,
    minHeight: 44
  },
  label: {
    color: appTheme.colors.surface,
    fontSize: 16,
    fontWeight: "700"
  },
  secondaryLabel: {
    color: appTheme.colors.primary
  },
  ghostLabel: {
    color: appTheme.colors.primary,
    fontSize: 14
  },
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.99 }]
  },
  disabled: {
    opacity: 0.6
  }
});
