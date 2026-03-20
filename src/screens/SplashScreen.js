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
      <LinearGradient colors={["#0B3C5D", "#145F8D"]} style={styles.container}>
        <Animated.View style={[styles.logoCircle, { transform: [{ scale: pulseAnim }] }]}>
          <Text style={styles.logoEmoji}>🛡️</Text>
        </Animated.View>
        <Text style={styles.title}>GigShield AI</Text>
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
    backgroundColor: "rgba(255,255,255,0.18)",
    borderRadius: appTheme.radius.pill,
    height: 92,
    justifyContent: "center",
    marginBottom: appTheme.spacing.lg,
    width: 92
  },
  logoEmoji: {
    fontSize: 42
  },
  title: {
    color: appTheme.colors.surface,
    fontSize: 36,
    fontWeight: "700"
  },
  subtitle: {
    color: "#D8EAF5",
    fontSize: 15,
    fontWeight: "600",
    marginTop: appTheme.spacing.xs
  },
  loadingTrack: {
    backgroundColor: "rgba(255,255,255,0.2)",
    borderRadius: appTheme.radius.pill,
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
