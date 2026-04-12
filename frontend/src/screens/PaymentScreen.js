import React, { useEffect, useMemo } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";

import Button from "../components/Button";
import { useAppContext } from "../context/AppContext";
import { appTheme } from "../styles/theme";

export default function PaymentScreen({ navigation, route }) {
  const { refreshPolicy } = useAppContext();
  const checkoutUrl = route?.params?.checkoutUrl || "";
  const orderId = route?.params?.orderId || "";

  const isValidUrl = useMemo(() => /^https?:\/\//i.test(checkoutUrl), [checkoutUrl]);

  useFocusEffect(
    React.useCallback(() => {
      let active = true;
      let timer = null;

      const pollPaymentStatus = async () => {
        while (active) {
          const latestPolicy = await refreshPolicy().catch(() => null);
          if ((latestPolicy?.paymentStatus || "pending") === "success") {
            navigation.goBack();
            return;
          }

          await new Promise((resolve) => {
            timer = setTimeout(resolve, 2500);
          });
        }
      };

      pollPaymentStatus().catch(() => {});

      return () => {
        active = false;
        if (timer) {
          clearTimeout(timer);
        }
      };
    }, [navigation, refreshPolicy])
  );

  if (!isValidUrl) {
    return (
      <SafeAreaView style={styles.screen}>
        <View style={styles.centered}>
          <Text style={styles.title}>Unable to load Razorpay checkout</Text>
          <Text style={styles.meta}>Please return and retry payment.</Text>
          <Button onPress={() => navigation.goBack()} style={styles.actionButton} title="Back" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.headerInfo}>
        <Text style={styles.title}>Complete Payment</Text>
        <Text style={styles.meta}>{orderId ? `Order: ${orderId}` : "Opening Razorpay checkout"}</Text>
      </View>
      <WebView
        source={{ uri: checkoutUrl }}
        javaScriptEnabled
        domStorageEnabled
        startInLoadingState
        renderLoading={() => (
          <View style={styles.loaderWrap}>
            <ActivityIndicator color={appTheme.colors.accentPrimary} size="large" />
            <Text style={styles.meta}>Loading Razorpay UI...</Text>
          </View>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: appTheme.colors.background
  },
  headerInfo: {
    paddingHorizontal: appTheme.spacing.lg,
    paddingTop: appTheme.spacing.sm,
    paddingBottom: appTheme.spacing.sm
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: appTheme.spacing.lg
  },
  loaderWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: appTheme.spacing.sm,
    backgroundColor: appTheme.colors.background
  },
  title: {
    color: appTheme.colors.textPrimary,
    fontFamily: "Orbitron_600SemiBold",
    fontSize: 18
  },
  meta: {
    color: appTheme.colors.textSecondary,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: 4
  },
  actionButton: {
    marginTop: appTheme.spacing.md,
    minWidth: 140
  }
});
