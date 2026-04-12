import React, { useMemo, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import Button from "../components/Button";
import { useAppContext } from "../context/AppContext";
import { verifyPayment } from "../services/insuranceApi";
import { appTheme } from "../styles/theme";

export default function PaymentScreen({ navigation, route }) {
  const { authToken, refreshPolicy } = useAppContext();
  const orderId = route?.params?.orderId || "";
  const amountPaise = Number(route?.params?.amount || 0);
  const fallbackPaymentId = route?.params?.paymentId || "";
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentError, setPaymentError] = useState("");

  const amountRupees = useMemo(() => (amountPaise > 0 ? (amountPaise / 100).toFixed(2) : "0.00"), [amountPaise]);

  const onPayNow = async () => {
    if (!authToken) {
      setPaymentError("Session expired. Please login again.");
      return;
    }

    if (!orderId) {
      setPaymentError("Missing order details. Please retry payment.");
      return;
    }

    setIsProcessing(true);
    setPaymentError("");

    try {
      // Simulated in-app payment success delay.
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const paymentId = fallbackPaymentId || `${orderId}_simulated`;

      await verifyPayment(authToken, {
        orderId,
        paymentId
      });

      await refreshPolicy(authToken);
      navigation.navigate("MainTabs", { screen: "Home" });
    } catch (error) {
      setPaymentError(error instanceof Error ? error.message : "Payment failed");
    } finally {
      setIsProcessing(false);
    }
  };

  if (!orderId) {
    return (
      <SafeAreaView style={styles.screen}>
        <View style={styles.centered}>
          <Text style={styles.title}>Unable to start payment</Text>
          <Text style={styles.meta}>Order details are missing. Please return and retry.</Text>
          <Button onPress={() => navigation.goBack()} style={styles.actionButton} title="Back" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.centered}>
        <Text style={styles.title}>Complete Payment</Text>
        <Text style={styles.meta}>{`Order: ${orderId}`}</Text>
        <Text style={styles.amount}>{`Amount: ₹${amountRupees}`}</Text>

        {isProcessing ? (
          <View style={styles.loaderWrap}>
            <ActivityIndicator color={appTheme.colors.accentPrimary} size="large" />
            <Text style={styles.meta}>Processing simulated payment...</Text>
          </View>
        ) : (
          <Button onPress={onPayNow} style={styles.actionButton} title="Pay Now" />
        )}

        {!!paymentError && <Text style={styles.errorText}>{paymentError}</Text>}
        <Button onPress={() => navigation.goBack()} style={styles.secondaryButton} title="Cancel" />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: appTheme.colors.background
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: appTheme.spacing.lg
  },
  loaderWrap: {
    alignItems: "center",
    justifyContent: "center",
    gap: appTheme.spacing.sm,
    marginTop: appTheme.spacing.md
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
  amount: {
    color: appTheme.colors.accentPrimary,
    fontFamily: "Orbitron_700Bold",
    fontSize: 24,
    marginTop: appTheme.spacing.sm
  },
  actionButton: {
    marginTop: appTheme.spacing.md,
    minWidth: 140
  },
  secondaryButton: {
    marginTop: appTheme.spacing.sm,
    minWidth: 140
  },
  errorText: {
    color: appTheme.colors.danger,
    fontFamily: "Rajdhani_600SemiBold",
    fontSize: 14,
    marginTop: appTheme.spacing.sm,
    textAlign: "center"
  }
});
