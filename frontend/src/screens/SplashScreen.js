import React, { useEffect, useRef } from "react";
import { Animated, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";

import { appTheme } from "../styles/theme";

export default function SplashScreen() {
  const pulseAnim = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          duration: 700,
          toValue: 1.1,
          useNativeDriver: true
        }),
        Animated.timing(pulseAnim, {
          duration: 700,
          toValue: 0.9,
          useNativeDriver: true
        })
      ])
    );

    pulseLoop.start();

    return () => {
      pulseLoop.stop();
    };
  }, [pulseAnim]);

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient colors={[appTheme.colors.gradientA, appTheme.colors.gradientB]} style={styles.container}>
        <Animated.View style={[styles.logoCircle, { transform: [{ scale: pulseAnim }] }]}>
          <Text style={styles.logoEmoji}>🛡️</Text>
        </Animated.View>
        <Text style={styles.title}>GuardGig</Text>
        <Text style={styles.subtitle}>Parametric Insurance for Gig Workers</Text>
        <View style={styles.loadingTrack}>
          <Animated.View style={[styles.loadingBar, { transform: [{ scaleX: pulseAnim }] }]} />
        </View>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1
  },
  container: {
    alignItems: "center",
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: appTheme.spacing.lg
  },
  logoCircle: {
    alignItems: "center",
    backgroundColor: appTheme.colors.overlaySoft,
    borderColor: appTheme.colors.borderStrong,
    borderRadius: appTheme.radius.pill,
    borderWidth: 1,
    height: 92,
    justifyContent: "center",
    marginBottom: appTheme.spacing.lg,
    width: 92,
    ...appTheme.shadows.glow
  },
  logoEmoji: {
    fontSize: 42
  },
  title: {
    color: appTheme.colors.textPrimary,
    ...appTheme.typography.display
  },
  subtitle: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 16,
    marginTop: appTheme.spacing.xs
  },
  loadingTrack: {
    backgroundColor: appTheme.colors.overlaySoft,
    borderColor: appTheme.colors.borderSubtle,
    borderRadius: appTheme.radius.pill,
    borderWidth: 1,
    height: 8,
    marginTop: appTheme.spacing.xl,
    overflow: "hidden",
    width: 150
  },
  loadingBar: {
    backgroundColor: appTheme.colors.accent,
    height: 8,
    width: 150
  }
});
