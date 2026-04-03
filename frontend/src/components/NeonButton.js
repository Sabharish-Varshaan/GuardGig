import React from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text } from "react-native";
import { LinearGradient } from "expo-linear-gradient";

import { appTheme } from "../styles/theme";

export default function NeonButton({
  title,
  onPress,
  variant = "primary",
  style,
  disabled = false,
  loading = false
}) {
  const isSecondary = variant === "secondary";
  const isGhost = variant === "ghost";

  const labelStyle = [
    styles.label,
    isSecondary ? styles.secondaryLabel : null,
    isGhost ? styles.ghostLabel : null
  ];

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
        {loading ? (
          <ActivityIndicator color={appTheme.colors.textPrimary} />
        ) : (
          <Text style={labelStyle}>{title}</Text>
        )}
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
        colors={[appTheme.colors.gradientCyanStart, appTheme.colors.gradientCyanEnd]}
        end={{ x: 1, y: 1 }}
        start={{ x: 0, y: 0 }}
        style={styles.gradientButton}
      >
        {loading ? <ActivityIndicator color={appTheme.colors.bgPrimary} /> : <Text style={labelStyle}>{title}</Text>}
      </LinearGradient>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    borderRadius: appTheme.radius.input,
    width: "100%",
    minHeight: 54,
    overflow: "hidden"
  },
  gradientButton: {
    alignItems: "center",
    justifyContent: "center",
    minHeight: 56,
    paddingHorizontal: appTheme.spacing.sm
  },
  secondaryButton: {
    alignItems: "center",
    backgroundColor: appTheme.colors.bgElevated,
    borderColor: appTheme.colors.borderStrong,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: appTheme.spacing.sm
  },
  ghostButton: {
    alignItems: "center",
    borderColor: appTheme.colors.borderSubtle,
    borderRadius: appTheme.radius.input,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 48,
    paddingHorizontal: appTheme.spacing.sm
  },
  label: {
    color: appTheme.colors.bgPrimary,
    fontFamily: "Rajdhani_700Bold",
    fontSize: 18,
    letterSpacing: 0.4
  },
  secondaryLabel: {
    color: appTheme.colors.textPrimary
  },
  ghostLabel: {
    color: appTheme.colors.accentPrimary,
    fontSize: 14
  },
  pressed: {
    opacity: 0.92,
    transform: [{ scale: 0.99 }]
  },
  disabled: {
    opacity: appTheme.motion.disabledOpacity
  }
});